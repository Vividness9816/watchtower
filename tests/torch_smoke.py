# tests/torch_smoke.py — CPU-only smoke of the tiny-GPT stack: build a small corpus, fit the
# tokenizer, one GPT forward/backward step. Catches torch/API breakage without a real train
# (a full train needs a GPU and stays out of CI). Run: pip install torch (CPU wheel is fine).
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import torch  # noqa: E402
from data import build_corpus  # noqa: E402
from gpt import GPT, GPTConfig, CharTokenizer  # noqa: E402


def main():
    text = build_corpus(20)                      # deterministic (seeded) synthetic docs
    tok = CharTokenizer.fit(text)
    ids = torch.tensor([tok.encode(text[:65])], dtype=torch.long)
    cfg = GPTConfig(vocab_size=tok.vocab_size, block_size=64,
                    n_layer=2, n_head=2, n_embd=32, dropout=0.0)
    model = GPT(cfg)
    logits, loss = model(ids[:, :-1], ids[:, 1:])
    loss.backward()
    assert logits.shape == (1, ids.shape[1] - 1, tok.vocab_size), logits.shape
    assert loss.item() > 0 and all(p.grad is not None for p in model.parameters()
                                   if p.requires_grad), "backward produced no grads"
    print(f"torch smoke ok — loss {loss.item():.3f}, params {model.num_params():,}")


if __name__ == "__main__":
    main()
