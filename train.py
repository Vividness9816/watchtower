import math
import os

import torch

import schema
from data import build_corpus
from gpt import GPT, GPTConfig, CharTokenizer

# ----------------------------------------------------------------- config (tweak me)
batch_size   = 64
block_size   = 256
max_iters    = 3000
eval_interval = 250
eval_iters   = 50
learning_rate = 3e-4
min_lr       = 3e-5
warmup_iters = 150
weight_decay = 0.1
grad_clip    = 1.0
n_layer, n_head, n_embd, dropout = 6, 6, 384, 0.1

device = "cuda" if torch.cuda.is_available() else "cpu"
# bf16 on Blackwell needs no GradScaler; fall back to fp32 on CPU.
use_bf16 = device == "cuda" and torch.cuda.is_bf16_supported()
ctx_dtype = torch.bfloat16 if use_bf16 else torch.float32
torch.manual_seed(1337)


def get_lr(it):
    if it < warmup_iters:
        return learning_rate * (it + 1) / warmup_iters
    if it > max_iters:
        return min_lr
    ratio = (it - warmup_iters) / (max_iters - warmup_iters)
    coeff = 0.5 * (1.0 + math.cos(math.pi * ratio))   # cosine decay 1 -> 0
    return min_lr + coeff * (learning_rate - min_lr)


def main():
    # --- data ---
    if not os.path.exists("corpus.txt"):
        print("corpus.txt missing - generating 8000 docs")
        open("corpus.txt", "w", encoding="utf-8").write(build_corpus(8000))
    text = open("corpus.txt", "r", encoding="utf-8").read()
    tok = CharTokenizer.fit(text)
    tok.save("vocab.json")
    data = torch.tensor(tok.encode(text), dtype=torch.long)
    n = int(0.9 * len(data))
    train_data, val_data = data[:n], data[n:]
    print(f"device={device} dtype={ctx_dtype} vocab={tok.vocab_size} "
          f"tokens(train/val)={len(train_data):,}/{len(val_data):,}")

    def get_batch(split):
        d = train_data if split == "train" else val_data
        ix = torch.randint(len(d) - block_size - 1, (batch_size,))
        x = torch.stack([d[i:i + block_size] for i in ix])
        y = torch.stack([d[i + 1:i + 1 + block_size] for i in ix])
        return x.to(device), y.to(device)

    # --- model ---
    cfg = GPTConfig(vocab_size=tok.vocab_size, block_size=block_size,
                    n_layer=n_layer, n_head=n_head, n_embd=n_embd, dropout=dropout)
    model = GPT(cfg).to(device)
    print(f"model params: {model.num_params()/1e6:.2f}M")

    # weight decay only on 2D matmul weights, not biases/layernorm/embeddings
    decay, nodecay = [], []
    for p in model.parameters():
        (decay if p.dim() >= 2 else nodecay).append(p)
    optimizer = torch.optim.AdamW(
        [{"params": decay, "weight_decay": weight_decay},
         {"params": nodecay, "weight_decay": 0.0}],
        lr=learning_rate, betas=(0.9, 0.95),
    )

    @torch.no_grad()
    def estimate_loss():
        model.eval()
        out = {}
        for split in ("train", "val"):
            losses = torch.zeros(eval_iters)
            for k in range(eval_iters):
                x, y = get_batch(split)
                with torch.autocast(device_type=device, dtype=ctx_dtype) if device == "cuda" else _null():
                    _, loss = model(x, y)
                losses[k] = loss.item()
            out[split] = losses.mean().item()
        model.train()
        return out

    def sample_report():
        snap = schema.synthetic_snapshot(__import__("random").Random())
        prompt = f"INPUT\n{schema.serialize_metrics(snap)}\nREPORT\n"
        ids = torch.tensor([tok.encode(prompt)], dtype=torch.long, device=device)
        out = model.generate(ids, max_new_tokens=200, temperature=0.7,
                             top_k=40, eos_id=tok.eos_id)
        txt = tok.decode(out[0].tolist())
        return txt.split("REPORT\n")[-1].split("\x03")[0]

    # --- loop ---
    model.train()
    for it in range(max_iters + 1):
        for g in optimizer.param_groups:
            g["lr"] = get_lr(it)

        if it % eval_interval == 0 or it == max_iters:
            losses = estimate_loss()
            print(f"iter {it:5d} | train {losses['train']:.4f} | val {losses['val']:.4f} "
                  f"| lr {get_lr(it):.2e}")
            print("   sample:", sample_report().replace("\n", " ")[:240])
            model.train()  # generate() left the model in eval(); resume training mode

        x, y = get_batch("train")
        with torch.autocast(device_type=device, dtype=ctx_dtype) if device == "cuda" else _null():
            _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

    torch.save({"model": model.state_dict(), "config": cfg.__dict__}, "ckpt.pt")
    print("saved ckpt.pt + vocab.json")


class _null:
    """no-op context manager for the CPU path (autocast cuda only)."""
    def __enter__(self): return None
    def __exit__(self, *a): return False


if __name__ == "__main__":
    main()