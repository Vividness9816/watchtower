# Watch Tower — Recreate From Scratch (Linux)

A complete, copy-paste guide to rebuild this project on a fresh Linux workstation on a different
network. Every file's full contents are included; every command shows its expected output. Work
top to bottom.

> Sibling guide: `RECREATE-WINDOWS.md`. This file is Linux-only. The **machine-learning core,
> UI, and chat brain are identical across both**; only the *collectors* (live sensors), a couple
> of paths, and the scheduler differ. Where a file is identical to Windows it is still printed
> here in full so this guide is standalone.

---

## 0. What you are building

**Watch Tower** = three layers:

1. **Truth layer (`sysdiag` + `collectors/`)** — scripts that read real sensors and emit JSON;
   `rules.py` turns JSON into severity-ranked findings.
2. **A from-scratch character-level GPT (`gpt.py` + `train.py`)** — trained on *synthetic*
   snapshots, fully offline, no downloads.
3. **A big-model chat brain (`brain.py` + `context.py`)** — talks to **Ollama** running
   `qwen2.5:32b` locally, grounded in the live snapshot + findings. CLI (`chat.py`) + Gradio web
   app (`app.py`) with a live panel and history graph.

```
collectors/*.py ──► sysdiag.py ──► snapshot{json} ──► rules.py ──► findings[]
                                      │
          ┌───────────────────────────┼───────────────────────────────┐
          ▼                           ▼                               ▼
   schema.serialize ─► tiny GPT   context.build ─► brain.ask ─► Ollama qwen2.5:32b
   (train.py/infer.py)             (chat.py CLI + app.py web UI + history graph)
```

The tiny GPT (you train it, ~10 MB) and the 32B Ollama model (downloaded, ~19 GB) are
independent — run either, both, or neither.

---

## 1. Prerequisites

```bash
# Debian/Ubuntu shown; translate to your distro's package manager.
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git lm-sensors curl
sudo sensors-detect --auto          # one-time: probe temp/fan chips for lm-sensors
```

| Tool | Why | Install / check |
|---|---|---|
| **Python 3.10+** | runs everything | `python3 --version` |
| **NVIDIA driver + CUDA GPU** | trains the GPT; runs the 32B model | `nvidia-smi` must print your GPU |
| **Ollama** | serves the 32B chat model | `curl -fsSL https://ollama.com/install.sh \| sh` |
| **lm-sensors** | CPU temp + fan RPM (`collectors/sensors.py`) | `sensors` must print temps |
| **Docker** *(optional)* | `docker`/`k3s` collectors | distro docker + add yourself to the `docker` group |

Verify:
```bash
python3 --version
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
ollama --version
sensors | head
```
Expected (yours differ):
```
Python 3.12.3
<GPU>, <VRAM>
ollama version is 0.30.8
coretemp-isa-0000
Package id 0:  +41.0°C  (high = +100.0°C, crit = +100.0°C)
```
> If `sensors` shows no CPU temp, re-run `sudo sensors-detect` and load the suggested modules.

---

## 2. Create the project folder

```bash
mkdir -p ~/sysdiag/collectors ~/sysdiag/docs
cd ~/sysdiag
```

All paths below are relative to `~/sysdiag`.

---

## 3. The machine-learning core (offline tiny GPT) — identical to Windows

These six files have **no OS-specific code**. Paste them exactly.

### `schema.py`
```python
import random

EOS = "\x03"  # end-of-document marker; one reserved control char


def _g(snap, *path, default=0):
    """Dig snap['a']['b']... returning default (0) for any missing/None step."""
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def serialize_metrics(snap: dict) -> str:
    """The exact INPUT text the model trains and runs on. Keep it stable forever."""
    return "\n".join([
        f"cpu_load={int(_g(snap,'cpu','load'))} cpu_temp={int(_g(snap,'sensors','cpu_temp'))} "
        f"mem_pct={int(_g(snap,'mem','pct'))}",
        f"gpu_util={int(_g(snap,'gpu','util'))} gpu_temp={int(_g(snap,'gpu','temp'))} "
        f"gpu_power={int(_g(snap,'gpu','power'))} gpu_vram={int(_g(snap,'gpu','vram_pct'))}",
        f"disk_C={int(_g(snap,'disk','C'))} whea_errors={int(_g(snap,'whea','recent_errors'))}",
    ])


def summarize(snap: dict) -> str:
    """One-line human summary embedded in every report (training label + runtime)."""
    return (f"CPU {int(_g(snap,'cpu','load'))}% / {int(_g(snap,'sensors','cpu_temp'))}C, "
            f"GPU {int(_g(snap,'gpu','util'))}% / {int(_g(snap,'gpu','temp'))}C / "
            f"{int(_g(snap,'gpu','power'))}W, RAM {int(_g(snap,'mem','pct'))}%, "
            f"disk C {int(_g(snap,'disk','C'))}%.")


def synthetic_snapshot(rng: random.Random) -> dict:
    """A plausible random machine state in the SAME nested shape the real collectors emit.
    ~35% are nudged hot so the corpus contains WARNING/CRITICAL examples to learn from."""
    hot = rng.random() < 0.35
    return {
        "cpu":     {"load": rng.randint(2, 100)},
        "sensors": {"cpu_temp": rng.randint(88, 101) if hot and rng.random() < 0.5 else rng.randint(35, 80)},
        "mem":     {"pct": rng.randint(86, 99) if hot and rng.random() < 0.4 else rng.randint(10, 80)},
        "gpu":     {"util": rng.randint(0, 100),
                    "temp": rng.randint(80, 92) if hot and rng.random() < 0.5 else rng.randint(30, 78),
                    "power": rng.randint(40, 575), "vram_pct": rng.randint(3, 99)},
        "disk":    {"C": rng.randint(85, 99) if hot and rng.random() < 0.3 else rng.randint(20, 84)},
        "whea":    {"recent_errors": 0 if rng.random() < 0.85 else rng.randint(1, 5)},
    }


def demo():  # train/serve symmetry check
    rng = random.Random(0)
    real = {"cpu": {"load": 5}, "sensors": {"cpu_temp": 45}, "mem": {"pct": 43},
            "gpu": {"util": 3, "temp": 39, "power": 64, "vram_pct": 12},
            "disk": {"C": 95}, "whea": {"recent_errors": 0}}
    for snap in (synthetic_snapshot(rng), real):
        s = serialize_metrics(snap)
        assert s.count("\n") == 2 and "cpu_load=" in s, "serialization shape drifted"
    print("schema ok")


if __name__ == "__main__":
    demo()
```

### `rules.py`
```python
# (warn, crit). THIS is your per-machine tuning knob — edit for your silicon.
THRESH = {
    "cpu_temp": (90, 98),   # <CPU> TjMax ~100
    "gpu_temp": (80, 88),   # <GPU> edge
    "mem_pct":  (85, 95),
    "disk_pct": (85, 95),
}


def _get(snap, *path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def diagnose(snap: dict) -> list[dict]:
    out = []

    def chk(value, key, label, unit="C"):
        lim = THRESH.get(key)
        if value is None or lim is None:
            return
        warn, crit = lim
        if value >= crit:
            out.append({"level": "CRIT", "what": label, "value": value, "limit": crit, "unit": unit})
        elif value >= warn:
            out.append({"level": "WARN", "what": label, "value": value, "limit": warn, "unit": unit})

    chk(_get(snap, "sensors", "cpu_temp"), "cpu_temp", "CPU temp")
    chk(_get(snap, "gpu", "temp"), "gpu_temp", "GPU temp")
    chk(_get(snap, "mem", "pct"), "mem_pct", "RAM", "%")
    disk = snap.get("disk", {})
    if isinstance(disk, dict):
        for mount, pct in disk.items():
            chk(pct, "disk_pct", f"disk {mount}", "%")

    whea = _get(snap, "whea", "recent_errors")
    if whea:
        out.append({"level": "CRIT", "what": "WHEA hardware errors", "value": whea, "limit": "", "unit": ""})

    cpu_temp = _get(snap, "sensors", "cpu_temp")
    fans = _get(snap, "sensors", "fans") or {}
    if cpu_temp and cpu_temp >= 90 and fans and min(fans.values()) == 0:
        out.append({"level": "CRIT", "what": "cooling (hot + stalled fan)", "value": cpu_temp, "limit": "", "unit": "C"})

    if "net" in snap and _get(snap, "net", "ping_ms") is None:
        out.append({"level": "CRIT", "what": "internet (1.1.1.1)", "value": "no reply", "limit": "", "unit": ""})

    for k, v in snap.items():
        if isinstance(v, dict) and "error" in v:
            out.append({"level": "WARN", "what": f"{k} sensor", "value": v["error"], "limit": "", "unit": ""})

    return out


def demo():  # a hot GPU MUST raise CRIT
    hot = {"gpu": {"temp": 99}, "net": {"ping_ms": 12}, "whea": {"recent_errors": 0}}
    assert any(f["level"] == "CRIT" for f in diagnose(hot)), "rule engine broken"
    print("rules ok")


if __name__ == "__main__":
    demo()
```

### `data.py`
```python
import sys, random
import schema, rules
from schema import EOS

DOC_TMPL = "INPUT\n{metrics}\nREPORT\n{report}" + EOS

_OPEN = {
    "OK":       ["All systems nominal.", "Everything looks healthy.", "Hardware is running clean."],
    "WARNING":  ["Heads up - something needs attention.", "One subsystem is running warm."],
    "CRITICAL": ["Critical condition detected.", "Something is in the red."],
}


def render_report(snap, findings, rng) -> str:
    st = "CRITICAL" if any(f["level"] == "CRIT" for f in findings) else "WARNING" if findings else "OK"
    lines = [f"{st}: {rng.choice(_OPEN[st])}", schema.summarize(snap)]
    for f in findings:
        verb = "is critical at" if f["level"] == "CRIT" else "is elevated at"
        if isinstance(f["limit"], (int, float)):
            lines.append(f"{f['what']} {verb} {f['value']}{f['unit']} (limit {f['limit']}{f['unit']}).")
        else:
            lines.append(f"{f['what']}: {f['value']}.")
    if st == "OK":
        lines.append(rng.choice(["No action needed.", "Continue normal operation."]))
    return " ".join(lines)


def build_corpus(n_docs: int, seed: int = 1337) -> str:
    rng = random.Random(seed)
    docs = []
    for _ in range(n_docs):
        snap = schema.synthetic_snapshot(rng)
        docs.append(DOC_TMPL.format(metrics=schema.serialize_metrics(snap),
                                    report=render_report(snap, rules.diagnose(snap), rng)))
    return "".join(docs)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    text = build_corpus(n)
    with open("corpus.txt", "w", encoding="utf-8") as f:
        f.write(text)
    n_alert = text.count("CRITICAL:") + text.count("WARNING:")
    print(f"wrote corpus.txt: {n} docs, {len(text):,} chars, "
          f"{len(set(text))} unique chars, ~{n_alert} with alerts")
    print("--- sample document ---")
    print(text.split(EOS)[0])


if __name__ == "__main__":
    main()
```

### `gpt.py`
```python
from __future__ import annotations
import json
import math
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.nn import functional as F

from schema import EOS  # document separator / end-of-sequence marker


class CharTokenizer:
    """One integer per character. Fully transparent. Always includes EOS in the vocab."""

    def __init__(self, itos: list[str]):
        self.itos = itos
        self.stoi = {ch: i for i, ch in enumerate(itos)}

    @classmethod
    def fit(cls, text: str) -> "CharTokenizer":
        chars = sorted(set(text) | {EOS})
        return cls(chars)

    @property
    def vocab_size(self) -> int:
        return len(self.itos)

    @property
    def eos_id(self) -> int:
        return self.stoi[EOS]

    def encode(self, s: str) -> list[int]:
        return [self.stoi[c] for c in s if c in self.stoi]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"itos": self.itos}, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "CharTokenizer":
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f)["itos"])


@dataclass
class GPTConfig:
    vocab_size: int = 128
    block_size: int = 256
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384
    dropout: float = 0.1
    bias: bool = True


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head = cfg.n_head
        self.n_embd = cfg.n_embd
        self.c_attn = nn.Linear(cfg.n_embd, 3 * cfg.n_embd, bias=cfg.bias)
        self.c_proj = nn.Linear(cfg.n_embd, cfg.n_embd, bias=cfg.bias)
        self.attn_dropout = nn.Dropout(cfg.dropout)
        self.resid_dropout = nn.Dropout(cfg.dropout)
        self.register_buffer(
            "tril",
            torch.tril(torch.ones(cfg.block_size, cfg.block_size)).view(1, 1, cfg.block_size, cfg.block_size),
        )

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)
        hs = C // self.n_head
        q = q.view(B, T, self.n_head, hs).transpose(1, 2)
        k = k.view(B, T, self.n_head, hs).transpose(1, 2)
        v = v.view(B, T, self.n_head, hs).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(hs))
        att = att.masked_fill(self.tril[:, :, :T, :T] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        att = self.attn_dropout(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.resid_dropout(self.c_proj(y))


class MLP(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.c_fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd, bias=cfg.bias)
        self.c_proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd, bias=cfg.bias)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x):
        return self.dropout(self.c_proj(F.gelu(self.c_fc(x))))


class Block(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.ln_1 = nn.LayerNorm(cfg.n_embd, bias=cfg.bias)
        self.attn = CausalSelfAttention(cfg)
        self.ln_2 = nn.LayerNorm(cfg.n_embd, bias=cfg.bias)
        self.mlp = MLP(cfg)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.n_embd)
        self.drop = nn.Dropout(cfg.dropout)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd, bias=cfg.bias)
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        self.tok_emb.weight = self.lm_head.weight   # weight tying
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def num_params(self) -> int:
        return sum(p.numel() for p in self.parameters()) - self.lm_head.weight.numel()

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.cfg.block_size, f"sequence {T} > block_size {self.cfg.block_size}"
        pos = torch.arange(T, device=idx.device)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        x = self.drop(x)
        for blk in self.blocks:
            x = blk(x)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-1
            )
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8, top_k=None, eos_id=None):
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / max(temperature, 1e-6)
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")
            probs = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, nxt), dim=1)
            if eos_id is not None and idx.size(0) == 1 and nxt.item() == eos_id:
                break
        return idx
```

### `train.py`
```python
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
use_bf16 = device == "cuda" and torch.cuda.is_bf16_supported()
ctx_dtype = torch.bfloat16 if use_bf16 else torch.float32
torch.manual_seed(1337)


def get_lr(it):
    if it < warmup_iters:
        return learning_rate * (it + 1) / warmup_iters
    if it > max_iters:
        return min_lr
    ratio = (it - warmup_iters) / (max_iters - warmup_iters)
    coeff = 0.5 * (1.0 + math.cos(math.pi * ratio))
    return min_lr + coeff * (learning_rate - min_lr)


def main():
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

    cfg = GPTConfig(vocab_size=tok.vocab_size, block_size=block_size,
                    n_layer=n_layer, n_head=n_head, n_embd=n_embd, dropout=dropout)
    model = GPT(cfg).to(device)
    print(f"model params: {model.num_params()/1e6:.2f}M")

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

    model.train()
    for it in range(max_iters + 1):
        for g in optimizer.param_groups:
            g["lr"] = get_lr(it)

        if it % eval_interval == 0 or it == max_iters:
            losses = estimate_loss()
            print(f"iter {it:5d} | train {losses['train']:.4f} | val {losses['val']:.4f} "
                  f"| lr {get_lr(it):.2e}")
            print("   sample:", sample_report().replace("\n", " ")[:240])
            model.train()

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
    def __enter__(self): return None
    def __exit__(self, *a): return False


if __name__ == "__main__":
    main()
```

### `infer.py`
```python
from __future__ import annotations
import argparse

import torch

import schema, rules, data
from gpt import GPT, GPTConfig, CharTokenizer


def load(ckpt_path="ckpt.pt", vocab_path="vocab.json", device=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok = CharTokenizer.load(vocab_path)
    ck = torch.load(ckpt_path, map_location=device)
    cfg = GPTConfig(**ck["config"])
    model = GPT(cfg).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    return {"model": model, "tok": tok, "device": device}


def generate_report(bundle, metrics_text: str, temperature=0.6, top_k=40,
                    max_new_tokens=220) -> str:
    model, tok, device = bundle["model"], bundle["tok"], bundle["device"]
    prompt = f"INPUT\n{metrics_text}\nREPORT\n"
    ids = torch.tensor([tok.encode(prompt)], dtype=torch.long, device=device)
    out = model.generate(ids, max_new_tokens=max_new_tokens, temperature=temperature,
                         top_k=top_k, eos_id=tok.eos_id)
    text = tok.decode(out[0].tolist())
    return text.split("REPORT\n")[-1].split("\x03")[0].strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--ckpt", default="ckpt.pt")
    ap.add_argument("--vocab", default="vocab.json")
    args = ap.parse_args()
    bundle = load(args.ckpt, args.vocab)

    if args.demo:
        import random
        snap = schema.synthetic_snapshot(random.Random())
        metrics = schema.serialize_metrics(snap)
        print("INPUT:\n" + metrics)
        print("\nGROUND TRUTH (rule-based):\n" + data.render_report(snap, rules.diagnose(snap), random.Random()))
        print("\nMODEL OUTPUT:\n" + generate_report(bundle, metrics))


if __name__ == "__main__":
    main()
```

---

## 4. The collectors (live Linux sensors)

The Linux collectors use **psutil**, **lm-sensors**, **nvidia-smi**, and the kernel log — no
PowerShell. They emit the same JSON shape as the Windows ones, so `rules.py`/`schema.py` are
unchanged. Install psutil into the venv (done in step 6).

> **Disk key note:** `schema.py` reads `disk.C` (a Windows drive letter). The Linux `disk.py`
> below **aliases the root filesystem `/` to the key `C`** so the trained model's `disk_C` input
> stays populated. Other mounts appear under their real mountpoint.

### `collectors/cpu.py`
```python
# collectors/cpu.py (Linux) — core counts + live load via psutil.
import json, psutil
try:
    load = int(round(psutil.cpu_percent(interval=0.3)))
    print(json.dumps({"cpu": {"cores": psutil.cpu_count(logical=False),
                              "logical": psutil.cpu_count(logical=True), "load": load}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))
```

### `collectors/mem.py`
```python
# collectors/mem.py (Linux) — RAM used% via psutil.
import json, psutil
try:
    print(json.dumps({"mem": {"pct": int(round(psutil.virtual_memory().percent))}}))
except Exception as e:
    print(json.dumps({"mem": {"error": str(e)}}))
```

### `collectors/disk.py`
```python
# collectors/disk.py (Linux) — used% per real mountpoint, with root '/' aliased to "C" so the
# trained model's `disk_C` input stays populated (schema.py is shared with the Windows build).
import json, psutil
out = {}
for part in psutil.disk_partitions(all=False):
    try:
        pct = int(round(psutil.disk_usage(part.mountpoint).percent))
    except (PermissionError, OSError):
        continue
    out["C" if part.mountpoint == "/" else part.mountpoint] = pct
print(json.dumps({"disk": out}))
```

### `collectors/gpu.py`
```python
# collectors/gpu.py (Linux) — nvidia-smi (ships with the driver). Absent GPU -> degrades.
import json, subprocess, shutil
smi = shutil.which("nvidia-smi")
try:
    if not smi:
        raise FileNotFoundError("nvidia-smi not found")
    q = "utilization.gpu,temperature.gpu,power.draw,memory.used,memory.total"
    row = subprocess.run([smi, f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=10).stdout.strip()
    u, t, p, used, total = (x.strip() for x in row.split(","))
    print(json.dumps({"gpu": {"util": int(float(u)), "temp": int(float(t)),
                              "power": int(float(p)),
                              "vram_pct": round(100 * float(used) / float(total))}}))
except Exception as e:
    print(json.dumps({"gpu": {"error": str(e)}}))
```

### `collectors/sensors.py`
```python
# collectors/sensors.py (Linux) — CPU package temp + fan RPM via lm-sensors (psutil).
# Needs `lm-sensors` installed and `sudo sensors-detect` run once.
import json, psutil
try:
    temps = psutil.sensors_temperatures()
    cpu = None
    for chip in ("coretemp", "k10temp", "zenpower"):
        for e in temps.get(chip, []):
            lbl = (e.label or "").lower()
            if e.current and ("package" in lbl or "tctl" in lbl):
                cpu = e.current
        if cpu is None and temps.get(chip):
            vals = [e.current for e in temps[chip] if e.current]
            cpu = max(vals) if vals else None
        if cpu is not None:
            break
    fans = {}
    for chip, entries in (psutil.sensors_fans() or {}).items():
        for e in entries:
            fans[f"{chip}:{e.label or 'fan'}"] = int(e.current)
    print(json.dumps({"sensors": {"cpu_temp": int(cpu) if cpu else None, "fans": fans}}))
except Exception as e:
    print(json.dumps({"sensors": {"error": str(e)}}))
```

### `collectors/net.py`
```python
# collectors/net.py (Linux) — ping 1.1.1.1 (stdlib) + link state (psutil).
import json, subprocess, re, psutil
def ping(host="1.1.1.1"):
    try:
        out = subprocess.run(["ping", "-c", "1", "-w", "2", host],
                             capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]\s*([\d.]+)\s*ms", out)
        return int(float(m.group(1))) if m else None
    except Exception:
        return None
def link():
    try:
        for name, s in psutil.net_if_stats().items():
            if name != "lo" and s.isup:
                return {"name": name, "speed": (f"{s.speed} Mbps" if s.speed else None)}
    except Exception:
        pass
    return {}
lk = link()
print(json.dumps({"net": {"ping_ms": ping(), "target": "1.1.1.1",
                          "up": bool(lk), "name": lk.get("name"), "speed": lk.get("speed")}}))
```

### `collectors/whea.py`  (Linux = MCE / kernel Hardware Error events)
```python
# collectors/whea.py (Linux) — Linux has no WHEA; the equivalent is MCE / "Hardware Error"
# events in the kernel log. Count recent ones from journalctl. Key stays "whea" so the shared
# schema.py/rules.py are unchanged. (journalctl -k may need the systemd-journal group / root.)
import json, subprocess
def main():
    try:
        out = subprocess.run(["journalctl", "-k", "--no-pager", "--since", "-24h"],
                             capture_output=True, text=True, timeout=15).stdout.lower()
        errs = sum(1 for ln in out.splitlines()
                   if "hardware error" in ln or "mce:" in ln or "machine check" in ln)
        print(json.dumps({"whea": {"recent_errors": errs, "latest": None}}))
    except Exception as e:
        print(json.dumps({"whea": {"error": str(e), "recent_errors": 0}}))
if __name__ == "__main__":
    main()
```

### `collectors/docker.py`  (optional; needs Docker + `docker` group)
```python
# collectors/docker.py (Linux) — Docker container state + live usage, parsed to numbers.
import json, re, subprocess, shutil, sys

DOCKER = shutil.which("docker")

_UNITS = {"b": 1, "kb": 1000, "mb": 1000**2, "gb": 1000**3, "tb": 1000**4,
          "kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4}


def _bytes(s):
    if not s:
        return None
    m = re.match(r"\s*([\d.]+)\s*([a-zA-Z]*)", s.strip())
    if not m or not m.group(1):
        return None
    return int(float(m.group(1)) * _UNITS.get(m.group(2).lower() or "b", 1))


def _pct(s):
    if not s:
        return None
    try:
        return float(s.strip().rstrip("%"))
    except ValueError:
        return None


def _pair(s):
    if not s or "/" not in s:
        return (None, None)
    a, b = s.split("/", 1)
    return (_bytes(a), _bytes(b))


def _int(s):
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return None


def _run(args):
    out = subprocess.run([DOCKER, *args], capture_output=True, text=True, timeout=30).stdout.strip()
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def main():
    if not DOCKER:
        print(json.dumps({"docker": {"error": "docker not found (installed? in the docker group?)"}}))
        return
    try:
        ps = _run(["ps", "--all", "--format", "{{json .}}"])
        try:
            stats = {s.get("Name"): s for s in _run(["stats", "--no-stream", "--format", "{{json .}}"])}
        except Exception:
            stats = {}
        containers = []
        for r in ps:
            st = stats.get(r.get("Names"), {})
            mem_used, mem_limit = _pair(st.get("MemUsage"))
            net_rx, net_tx = _pair(st.get("NetIO"))
            blk_r, blk_w = _pair(st.get("BlockIO"))
            containers.append({
                "name": r.get("Names"), "image": r.get("Image"), "status": r.get("Status"),
                "ports": r.get("Ports") or "", "cpu_pct": _pct(st.get("CPUPerc")),
                "mem_used_bytes": mem_used, "mem_limit_bytes": mem_limit, "mem_pct": _pct(st.get("MemPerc")),
                "net_rx_bytes": net_rx, "net_tx_bytes": net_tx,
                "blk_read_bytes": blk_r, "blk_write_bytes": blk_w, "pids": _int(st.get("PIDs")),
            })
        running = sum(1 for r in ps if str(r.get("Status", "")).startswith("Up"))
        print(json.dumps({"docker": {"running": running, "total": len(containers), "containers": containers}}))
    except Exception as e:
        print(json.dumps({"docker": {"error": str(e)}}))


def demo():
    assert _bytes("120MiB") == 125829120
    assert _pair("120MiB / 7.6GiB") == (125829120, int(7.6 * 1024**3))
    assert _int("12") == 12 and _int(None) is None
    print("docker parsers ok")


if __name__ == "__main__":
    (demo if "--test" in sys.argv else main)()
```

### `collectors/k3s.py`  (optional; native k3s)
```python
# collectors/k3s.py (Linux) — k3s runs natively. Uses `sudo -n` so it works unattended IF
# passwordless `k3s kubectl` is allowed; otherwise it degrades to an error finding. If your
# user already has KUBECONFIG set, change K3S_CMD to ["kubectl","get","pods","-A","-o","json"].
import json, subprocess
K3S_CMD = ["sudo", "-n", "k3s", "kubectl", "get", "pods", "-A", "-o", "json"]
def main():
    try:
        r = subprocess.run(K3S_CMD, capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            print(json.dumps({"k3s": {"error": (r.stderr or "kubectl failed").strip()[:200]}}))
            return
        items = json.loads(r.stdout).get("items", [])
        pods = [{"name": i.get("metadata", {}).get("name"),
                 "namespace": i.get("metadata", {}).get("namespace"),
                 "phase": i.get("status", {}).get("phase")} for i in items]
        running = sum(1 for p in pods if p["phase"] == "Running")
        print(json.dumps({"k3s": {"running": running, "total": len(pods), "pods": pods}}))
    except Exception as e:
        print(json.dumps({"k3s": {"error": str(e)}}))
if __name__ == "__main__":
    main()
```

### `collectors/usb.py`  (optional; `lsusb`)
```python
# collectors/usb.py (Linux) — USB device count via lsusb (apt install usbutils).
import json, subprocess
try:
    out = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=10).stdout
    print(json.dumps({"usb": {"devices": len([l for l in out.splitlines() if l.strip()]), "problems": 0}}))
except Exception as e:
    print(json.dumps({"usb": {"error": str(e)}}))
```

### `collectors/storage.py`  (optional; `smartctl`, usually needs root)
```python
# collectors/storage.py (Linux) — drive health via smartctl (apt install smartmontools).
# SMART usually needs root, so unprivileged this degrades to "unknown"/error.
import json, subprocess, shutil, glob
def main():
    sc = shutil.which("smartctl")
    if not sc:
        print(json.dumps({"storage": {"error": "smartctl not found (apt install smartmontools)"}}))
        return
    drives = []
    for dev in sorted(glob.glob("/dev/nvme[0-9]n1") + glob.glob("/dev/sd[a-z]")):
        try:
            out = subprocess.run([sc, "-H", dev], capture_output=True, text=True, timeout=15).stdout
            health = "PASSED" if "PASSED" in out else ("FAILED" if "FAILED" in out else "unknown")
            drives.append({"name": dev, "health": health})
        except Exception:
            pass
    print(json.dumps({"storage": {"drives": drives}}))
if __name__ == "__main__":
    main()
```

> **Windows-only collectors omitted on Linux:** `tpm.py` (Get-Tpm) and `me.py` (Intel ME driver)
> have no clean Linux equivalent and aren't used by the model or rules — simply don't create
> them. `sysdiag.py` globs whatever `collectors/*.py` exist, so a smaller set just means fewer
> keys in the snapshot; nothing breaks.

### `sysdiag.py` — aggregator + CLI (identical to Windows)
```python
import json, glob, subprocess, sys, pathlib, argparse
HERE = pathlib.Path(__file__).parent


def snapshot(only=None) -> dict:
    snap = {}
    pattern = str(HERE / "collectors" / (f"{only}.py" if only else "*.py"))
    for f in sorted(glob.glob(pattern)):
        try:
            out = subprocess.run([sys.executable, f], capture_output=True, text=True, timeout=25).stdout
            snap.update(json.loads(out))
        except Exception as e:
            snap.setdefault("_errors", []).append(f"{pathlib.Path(f).name}: {e}")
    return snap


def print_findings(snap):
    import rules
    findings = rules.diagnose(snap)
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
        return
    order = {"CRIT": 0, "WARN": 1}
    for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
        print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
              + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))


def narrate():
    import schema, infer
    snap = snapshot()
    bundle = infer.load()
    print(infer.generate_report(bundle, schema.serialize_metrics(snap)))
    print("\n--- findings (truth) ---")
    print_findings(snap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="diag", help="diag | net | report")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    if args.cmd == "report" and not args.no_llm:
        narrate()
        return
    snap = snapshot(only="net" if args.cmd == "net" else None)
    if args.json:
        print(json.dumps(snap, indent=2))
    else:
        print_findings(snap)


if __name__ == "__main__":
    main()
```

### `history.py` — log one snapshot to SQLite (identical to Windows)
```python
# history.py — append one snapshot to a SQLite history DB. Run on a timer (cron/systemd).
import sqlite3, json, time, pathlib
import sysdiag

DB = pathlib.Path(__file__).parent / "history.db"

def main():
    snap = sysdiag.snapshot()
    with sqlite3.connect(DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS snapshots (ts TEXT, json TEXT)")
        con.execute("INSERT INTO snapshots VALUES (?, ?)",
                    (time.strftime("%Y-%m-%dT%H:%M:%S"), json.dumps(snap)))
    print("logged", time.strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()
```

### `system_facts.md` — edit for YOUR machine
```markdown
# This machine

- CPU: <your CPU> (cores/threads, TjMax). Note what temps are normal under load.
- GPU: <your GPU>, <VRAM>. Note the edge temp limit and expected load temps.
- RAM: <size/speed>.
- Storage: root `/` on <drive>; other mounts.
- Role: <what this box does> — runs Ollama, maybe Docker/k3s.
- What I care about: failing components, thermal throttling, MCE hardware errors, disks filling, a fan stalling.
```

---

## 5. The chat brain (Ollama) + UI

### `art.py` — ASCII banner (identical; works in any ANSI terminal)
```python
# art.py — the Watch Tower banner, shared by the CLI (chat.py) and the web UI (app.py).
import os, shutil

if os.name == "nt":
    os.system("")   # enable ANSI in legacy Windows consoles; no-op elsewhere

LIGHT_BLUE = "\033[38;2;173;216;230m"
RESET = "\033[0m"

WATCH_TOWER = """
██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗    ████████╗ ██████╗ ██╗    ██╗███████╗██████╗
██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║    ╚══██╔══╝██╔═══██╗██║    ██║██╔════╝██╔══██╗
██║ █╗ ██║███████║   ██║   ██║     ███████║       ██║   ██║   ██║██║ █╗ ██║█████╗  ██████╔╝
██║███╗██║██╔══██║   ██║   ██║     ██╔══██║       ██║   ██║   ██║██║███╗██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║       ██║   ╚██████╔╝╚███╔███╔╝███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝
"""


def cli_banner():
    width = shutil.get_terminal_size((100, 20)).columns
    print(f"{LIGHT_BLUE}{WATCH_TOWER}\n{'─' * width}{RESET}")


def html_banner():
    return ('<pre style="color:#ADD8E6; line-height:1.05; font-size:11px; '
            'overflow-x:auto; margin:0; white-space:pre">' + WATCH_TOWER + '</pre>')


if __name__ == "__main__":
    cli_banner()
```
> Save as **UTF-8** so the box glyphs survive. Test: `python art.py`.

### `context.py` — grounding context (only the HOMELAB path differs from Windows)
```python
import json, pathlib
import rules

FACTS = pathlib.Path(__file__).parent / "system_facts.md"
HOMELAB = pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md"  # optional; missing = skipped

HOMELAB_TRIGGERS = ("docker", "container", "homelab", "compose", "traefik", "service",
                    "service", "service", "service", "service", "grafana", "service",
                    "k3s", "service", "vpn", "reverse proxy")


def _wants_homelab(message: str) -> bool:
    return any(t in message.lower() for t in HOMELAB_TRIGGERS)


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _snapshot() -> dict:
    try:
        import sysdiag
        return sysdiag.snapshot()
    except Exception as e:
        return {"_note": f"truth layer not built ({e}); showing stub.",
                "cpu": {"load": 0}, "sensors": {"cpu_temp": 0}, "mem": {"pct": 0},
                "gpu": {"util": 0, "temp": 0, "power": 0, "vram_pct": 0},
                "disk": {"C": 0}, "whea": {"recent_errors": 0}}


def snapshot_and_findings():
    snap = _snapshot()
    return snap, rules.diagnose(snap)


def build(message: str = "") -> str:
    snap, findings = snapshot_and_findings()
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        "LIVE SNAPSHOT (JSON, just collected):",
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    if _wants_homelab(message):
        homelab = _read(HOMELAB)
        if homelab:
            parts += ["", "HOMELAB REFERENCE (HOMELAB-COMPLETE-SETUP.md):", homelab]
    return "\n".join(parts)


if __name__ == "__main__":
    assert _wants_homelab("how's my docker stack?") and not _wants_homelab("is my GPU hot?")
    print(build())
```

### `brain.py` — Ollama call (system prompt adapted for Linux/bash/sudo)
```python
### brain.py — the chatbot brain. Qwen2.5-32B via Ollama, grounded in the live system state from context.py. READ-ONLY: nothing it returns is ever executed — its output is text shown to a human. ###

import json, urllib.request, urllib.error
import context

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:32b"            # Q4_K_M by default; ~19GB, fits a 32GB GPU

SYSTEM = """You are a hands-on hardware-diagnostics and troubleshooting expert for THIS
specific Linux workstation. You answer questions about its health and tell the user EXACTLY what
to do — as concrete, copy-pasteable steps.

How to answer — ALWAYS:
- Give numbered, step-by-step instructions. Assume the user copies and runs each step.
- For EVERY command state all four: (1) the shell — bash; (2) the exact command in a code block;
  (3) the folder to run it from — give the literal `cd` command when it matters; (4) whether it
  needs root. If it does, say so first and show it prefixed with `sudo` (or tell them to open a
  root shell) before that step.
- End with: what a successful result looks like, and the one thing to check if it fails.
- Prefer standard Linux tools (systemctl, journalctl, lm-sensors, smartctl, df, free, nvidia-smi)
  and the user's own `sysdiag` tool. Do NOT invent commands, flags, or file paths. If you're
  unsure a command exists or is safe, say so instead of guessing.
- BEFORE any destructive or risky step (deleting files, editing system config, killing processes,
  anything needing root), put a one-line warning so the user reads it before running.

Hard rules:
- You only ADVISE. You never run anything — the user runs the steps and decides.
- The FINDINGS list is deterministic ground truth from a rules engine. Trust it over your own
  inference; if you disagree with the findings, the findings win.
- Use the STATIC FACTS to judge what's normal for THIS machine and where things live.
- Ground every recommendation in the live snapshot + findings below; cite the actual numbers.
  If the data doesn't show something, say so. Never invent readings, events, or commands.

{ctx}"""

def _text(content):
    """Ollama's /api/chat needs content as a plain string; Gradio sometimes hands a
    list of parts (e.g. [{'type':'text','text':...}]) which Ollama 400s on."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return "" if content is None else str(content)


def ask(message, history):
    """Gradio ChatInterface fn (type='messages'): history is [{role,content}, ...]."""
    user_text = _text(message)
    msgs = [{"role": "system", "content": SYSTEM.format(ctx=context.build(user_text))}]
    msgs += [{"role": m["role"], "content": _text(m.get("content"))} for m in (history or [])]
    msgs.append({"role": "user", "content": user_text})
    body = json.dumps({"model": MODEL, "messages": msgs, "stream": False,
                       "keep_alive": "30m",
                       "options": {"temperature": 0.3, "num_ctx": 32768}}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"(Ollama returned HTTP {e.code}: {e.read().decode(errors='replace')[:300]})"
    except Exception as e:
        return f"(couldn't reach Ollama at {OLLAMA}: {e}. Is `ollama` running? Try `ollama ps`.)"


def demo():
    assert _text([{"type": "text", "text": "a"}, {"text": "b"}]) == "ab"
    assert _text("hi") == "hi" and _text(None) == ""
    reply = ask("Is anything wrong right now? One sentence.", [])
    assert isinstance(reply, str) and reply.strip(), "no reply from the brain"
    print("brain ok:", reply[:160])


if __name__ == "__main__":
    demo()
```

### `trends.py` — history → graph DataFrame (identical to Windows)
```python
# trends.py — read history.db and return time-series DataFrames for the UI graphs.
import json, sqlite3, pathlib, datetime
import pandas as pd

DB = pathlib.Path(__file__).parent / "history.db"

METRICS = {
    "CPU temp (C)":    ("sensors", "cpu_temp"),
    "CPU load (%)":    ("cpu", "load"),
    "GPU temp (C)":    ("gpu", "temp"),
    "GPU power (W)":   ("gpu", "power"),
    "GPU util (%)":    ("gpu", "util"),
    "GPU VRAM (%)":    ("gpu", "vram_pct"),
    "RAM used (%)":    ("mem", "pct"),
    "Disk C used (%)": ("disk", "C"),
    "Ping (ms)":       ("net", "ping_ms"),
    "WHEA errors":     ("whea", "recent_errors"),
}

RUNS = {"Last 10 runs": 10, "Last 25 runs": 25, "Last 50 runs": 50,
        "Last 100 runs": 100, "All runs": None}


def _dig(snap, path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def series(metric, runs_label="Last 25 runs"):
    path = METRICS.get(metric)
    if path is None or not DB.exists():
        return pd.DataFrame({"time": [], "value": [], "when": []})
    limit = RUNS.get(runs_label)
    query = "SELECT ts, json FROM snapshots ORDER BY ts DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = sqlite3.connect(DB).execute(query).fetchall()
    rows.reverse()
    times, values = [], []
    for ts, j in rows:
        try:
            v = _dig(json.loads(j), path)
        except Exception:
            v = None
        if v is not None:
            times.append(ts)
            values.append(v)
    t = pd.to_datetime(times)
    when = [x.strftime("%b %d, %H:%M:%S") for x in t]
    return pd.DataFrame({"time": t, "value": values, "when": when})


if __name__ == "__main__":
    df = series("CPU temp (C)", "Last 10 runs")
    assert list(df.columns) == ["time", "value", "when"] and len(df) <= 10
    print(df.tail())
```

### `app.py` — Gradio web dashboard (identical to Windows)
```python
"""app.py — Watch Tower: live stats, chat, and history graphs. READ-ONLY, 127.0.0.1 only."""
import gradio as gr
import schema, brain, context, art, trends


def stats_md() -> str:
    snap, findings = context.snapshot_and_findings()
    head = schema.summarize(snap)
    lines = [f"### Live\n{head}", "", "### Findings"]
    if findings:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            lines.append(f"- **[{f['level']}]** {f['what']}: {f['value']}{f['unit']}")
    else:
        lines.append("- OK — no findings")
    d = snap.get("docker", {})
    if d and "error" not in d:
        lines.append(f"\n**Docker:** {d.get('running')}/{d.get('total')} running")
    if "_note" in snap:
        lines.append(f"\n> {snap['_note']}")
    return "\n".join(lines)


def plot(metric, rng):
    return trends.series(metric, rng)


with gr.Blocks(title="Watch Tower") as app:
    gr.HTML(art.html_banner())
    gr.Markdown("# Watch Tower — your system, explained")
    with gr.Row():
        with gr.Column(scale=1):
            panel = gr.Markdown(stats_md())
            gr.Timer(5).tick(stats_md, outputs=panel)
        with gr.Column(scale=2):
            gr.ChatInterface(
                fn=brain.ask,
                title="Ask about this machine",
                examples=["Is anything overheating?",
                          "What's eating my disk space?",
                          "Are there any hardware errors?",
                          "Is my GPU temp normal for this card?"],
            )
    gr.Markdown("## History")
    with gr.Row():
        metric = gr.Dropdown(list(trends.METRICS), value="CPU temp (C)", label="Component / metric")
        runs = gr.Dropdown(list(trends.RUNS), value="Last 25 runs", label="Show")
    graph = gr.LinePlot(trends.series("CPU temp (C)", "Last 25 runs"),
                        x="time", y="value", tooltip=["when", "value"],
                        title="History", height=320)
    metric.change(plot, [metric, runs], graph)
    runs.change(plot, [metric, runs], graph)


if __name__ == "__main__":
    art.cli_banner()
    try:
        app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
    finally:
        import subprocess  # free the model's VRAM on clean exit (Ctrl+C)
        subprocess.run(["ollama", "stop", brain.MODEL], check=False)
```

### `chat.py` — CLI chat (identical to Windows)
```python
# chat.py — Watch Tower from the command line. Same model + live system context as the web UI.
import art, brain

PROMPT = "\033[38;2;173;216;230m❯\033[0m "   # light-blue prompt to match the banner


def main():
    art.cli_banner()
    print("Ask about this machine. Type 'exit' or Ctrl+C to quit.\n")
    history = []
    while True:
        try:
            msg = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if msg.strip().lower() in ("exit", "quit"):
            break
        if not msg.strip():
            continue
        reply = brain.ask(msg, history)
        print(f"\n{reply}\n")
        history += [{"role": "user", "content": msg},
                    {"role": "assistant", "content": reply}]


if __name__ == "__main__":
    try:
        main()
    finally:
        import subprocess  # free the model's VRAM on exit
        subprocess.run(["ollama", "stop", brain.MODEL], check=False)
```

### `.gitignore`
```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
ckpt.pt
*.pt
*.safetensors
history.db
*.db-journal
.env
.env.*
.DS_Store
```

### `requirements.txt`
```
torch
gradio
pandas
psutil
```

---

## 6. Build it — step by step (with expected output)

All commands run from `~/sysdiag`.

### 6.1 Virtual env + dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# torch for your CUDA (cu128 = CUDA 12.8; pick yours from pytorch.org). CPU-only? drop --index-url.
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install gradio pandas psutil
```
Confirm:
```bash
python -c "import torch,gradio,pandas,psutil; print('torch',torch.__version__,'cuda',torch.cuda.is_available()); print('gradio',gradio.__version__,'pandas',pandas.__version__)"
```
Expected:
```
torch 2.11.0+cu128 cuda True
gradio 6.19.0 pandas 3.0.3
```

### 6.2 Sanity-check pure-logic modules
```bash
python schema.py
python rules.py
python collectors/docker.py --test
```
Expected:
```
schema ok
rules ok
docker parsers ok
```

### 6.3 Generate the corpus
```bash
python data.py 8000
```
Expected:
```
wrote corpus.txt: 8000 docs, 2,055,944 chars, 80 unique chars, ~3900 with alerts
--- sample document ---
INPUT
cpu_load=70 cpu_temp=80 mem_pct=56
gpu_util=73 gpu_temp=67 gpu_power=209 gpu_vram=45
disk_C=69 whea_errors=0
REPORT
OK: Everything looks healthy. CPU 70% / 80C, GPU 73% / 67C / 209W, RAM 56%, disk C 69%. Continue normal operation.
```

### 6.4 Train the tiny GPT
```bash
python train.py
```
Expected (representative — exact losses vary; ~2-5 min on a CUDA GPU):
```
device=cuda dtype=torch.bfloat16 vocab=80 tokens(train/val)=1,850,349/205,595
model params: 10.79M
iter     0 | train 4.4xxx | val 4.4xxx | lr 2.00e-06
   sample: <gibberish at first>
...
iter  3000 | train 0.2xxx | val 0.2xxx | lr 3.00e-05
   sample: WARNING: One subsystem is running warm. ... CPU temp is elevated at 94C (limit 90C).
saved ckpt.pt + vocab.json
```
Writes `ckpt.pt` (~44 MB) + `vocab.json`.

### 6.5 Test the trained model
```bash
python infer.py --demo
```
Expected: an `INPUT`, a rule-based `GROUND TRUTH`, and a `MODEL OUTPUT` that closely matches it.

### 6.6 Run the live collectors
```bash
python collectors/cpu.py
python collectors/gpu.py
python collectors/sensors.py
python collectors/disk.py
python sysdiag.py
```
Expected (yours reflect your hardware; note `disk` root shown as `C`):
```
{"cpu": {"cores": 24, "logical": 32, "load": 6}}
{"gpu": {"util": 1, "temp": 36, "power": 57, "vram_pct": 11}}
{"sensors": {"cpu_temp": 41, "fans": {"coretemp:fan1": 900}}}
{"disk": {"C": 47, "/home": 62}}
[WARN] RAM: 87% (limit 85%)
```
> If `sensors` shows `cpu_temp: null`, lm-sensors didn't find a package sensor — run
> `sudo sensors-detect --auto` and `sensors` to confirm, then adjust the chip names in
> `collectors/sensors.py` if needed.

### 6.7 Full snapshot JSON
```bash
python sysdiag.py diag --json
```
Expected: a pretty-printed JSON object with `cpu`, `mem`, `disk`, `gpu`, `sensors`, `net`,
`whea`, (and `docker`/`k3s` if present). This is what `context.py` feeds the chat model.

---

## 7. Connect Ollama (the 32B chat model)

```bash
curl -fsSL https://ollama.com/install.sh | sh   # installs + starts the ollama systemd service
ollama pull qwen2.5:32b                          # ~19 GB
ollama run qwen2.5:32b "say OK"                  # expect: OK
ollama ps
```
Expected `ollama ps`:
```
NAME           ID    SIZE     PROCESSOR    CONTEXT    UNTIL
qwen2.5:32b    ...   28 GB    100% GPU     32768      30 minutes from now
```
> Same VRAM math as Windows: KV cache ≈ 256 KB/token (~8 GB at 32k); ~19 GB model + 8 GB ≈ 28 GB,
> fits a 32 GB GPU. Smaller GPU → set `num_ctx` to `16384`/`8192` in `brain.py`. `keep_alive: 30m`
> keeps it warm; `app.py`/`chat.py` `ollama stop` on clean exit.

Smoke-test:
```bash
python brain.py
```
Expected: `brain ok: <a real sentence about your machine's current state>`

### Choosing the chat model — US-built open-weight options

`brain.py` sets `MODEL = "qwen2.5:32b"` — a strong default, but Qwen is built by Alibaba (China).
To run a **US-built** model instead, `ollama pull <tag>` one of the open-weight families below, then
set `MODEL` to that tag and re-check `num_ctx` against your VRAM. They all run the same way through
Ollama; no other code changes.

> VRAM figures are **approximate**, at Ollama's default **Q4_K_M** quant, and cover the *weights
> only* — add KV cache for your `num_ctx` (~256 KB/token for a 32B; less for smaller models). If a
> model doesn't fit VRAM, Ollama spills layers to system RAM: slower, but it still runs. Tags and
> context lengths change over time — confirm with `ollama show <tag>` and the model card.

| Model (US company) | `ollama pull` tag | Params | Context | ~VRAM @ Q4 | Notes |
|---|---|---|---|---|---|
| Llama 3.2 (Meta) | `llama3.2:1b` · `:3b` | 1B · 3B | 128K | ~1 · ~2.5 GB | edge / CPU-friendly |
| Llama 3.1 (Meta) | `llama3.1:8b` | 8B | 128K | ~6 GB | best small all-rounder |
| Llama 3.3 (Meta) | `llama3.3:70b` | 70B | 128K | ~42 GB | ~405B quality at 70B |
| Llama 3.1 (Meta) | `llama3.1:70b` · `:405b` | 70B · 405B | 128K | ~42 · ~230 GB | 405B = multi-GPU / server |
| Llama 4 Scout (Meta) | `llama4:scout` | 109B MoE / 17B active | up to 10M | ~65 GB | MoE; very long context |
| Llama 4 Maverick (Meta) | `llama4:maverick` | 400B MoE / 17B active | 1M | ~240 GB | server / multi-GPU |
| Gemma 3 (Google) | `gemma3:1b·4b·12b·27b` | 1–27B | 128K (1B: 32K) | ~1 · ~3 · ~8 · ~17 GB | vision on 4B+; excellent |
| Gemma 2 (Google) | `gemma2:2b·9b·27b` | 2–27B | 8K | ~2 · ~6 · ~16 GB | older, short context |
| Phi-4 (Microsoft) | `phi4` | 14B | 16K | ~9 GB | strong reasoning per GB |
| Phi-4-mini (Microsoft) | `phi4-mini` | 3.8B | 128K | ~3 GB | small + long context |
| gpt-oss (OpenAI) | `gpt-oss:20b` · `:120b` | 21B · 117B MoE | 128K | ~14 · ~65 GB | OpenAI's open-weight reasoning models (MXFP4) |
| Nemotron (NVIDIA) | `nemotron:70b` | 70B | 128K | ~42 GB | NVIDIA-tuned Llama-3.1, RLHF |
| Nemotron-mini (NVIDIA) | `nemotron-mini:4b` | 4B | 4K | ~3 GB | on-device |
| Granite 3.3 (IBM) | `granite3.3:2b` · `:8b` | 2B · 8B | 128K | ~2 · ~5 GB | enterprise, tool-use |
| OLMo 2 (Allen AI) | `olmo2:7b` · `:13b` | 7B · 13B | 4K | ~5 · ~8 GB | fully open (data + weights) |
| DBRX (Databricks) | `dbrx` | 132B MoE / 36B active | 32K | ~80 GB | server-class MoE |

> **Not open-weight (can't `ollama pull`):** Anthropic Claude and OpenAI's flagship GPT are
> API-only — OpenAI's open release is **gpt-oss** (above). xAI published Grok-1 weights, but at 314B
> they're impractical here. Mistral/Mixtral (France), Qwen/DeepSeek (China), Command-R (Cohere,
> Canada) and Falcon (UAE) are excluded as non-US.

**Pick by capability:**

- **If hardware is no object** (≥48 GB VRAM, or multi-GPU / server): `llama3.1:405b` or
  `llama4:maverick` for frontier quality; **`llama3.3:70b`** or **`nemotron:70b`** as the best
  practical 70B; **`gpt-oss:120b`** for OpenAI-style reasoning; `dbrx` for a fast MoE. On a single
  ~32 GB GPU the strongest US options are **`gpt-oss:20b`**, **`gemma3:27b`**, or **`phi4`**.
- **If hardware is constrained** (8–16 GB VRAM, or CPU-only): **`llama3.1:8b`** or
  **`granite3.3:8b`** (8 GB class); **`gemma3:12b`** / **`phi4`** at ~12 GB; **`llama3.2:3b`** /
  **`gemma3:4b`** / **`phi4-mini`** for CPU-only or ≤8 GB. Keep `num_ctx` at `8192`–`16384` so the
  KV cache fits beside the weights.

Sizing rule: **weights (≈ the table's VRAM) + KV cache (`num_ctx`) ≤ your VRAM**, else lower
`num_ctx` in `brain.py` or accept CPU spillover. After pulling, set `MODEL = "<tag>"` and restart
`app.py` / `chat.py`.

---

## 8. Run it

```bash
python chat.py     # CLI: banner + ❯ prompt; ask "Is my GPU temp normal?"; 'exit' to quit
python app.py      # web: opens http://127.0.0.1:7860
```
Expected `app.py` console:
```
<light-blue WATCH TOWER banner>
* Running on local URL:  http://127.0.0.1:7860
```
Ctrl+C stops it (and frees VRAM). After editing any `.py`, **restart `app.py`** — Gradio caches
the loaded modules.

---

## 9. Schedule history logging (the graph's data)

Fill `history.db` every ~15 min. Easiest is **cron**:
```bash
crontab -e
# add this line (absolute paths; venv python):
*/15 * * * * cd ~/sysdiag && ~/sysdiag/.venv/bin/python history.py >> ~/sysdiag/history.log 2>&1
```
Or a **systemd timer** (`~/.config/systemd/user/watchtower.service` + `.timer`, then
`systemctl --user enable --now watchtower.timer`).

Verify one manual run:
```bash
python history.py
```
Expected:
```
logged 21:22:15
```
After a few runs the History graph fills in; pick a metric + "Last N runs" and **hover** a point
for its date + time.

---

## 10. The ASCII art / banner (recap)

- `art.py` is the banner — light-blue truecolor (`\033[38;2;173;216;230m`), used by `chat.py`
  (`cli_banner()`) and `app.py` (`html_banner()`). Save as UTF-8 so the box glyphs survive
  (`python art.py` to test). The `os.name == "nt"` check is a no-op on Linux.
- The web banner is the same art in a `<pre>`, injected via `gr.HTML(art.html_banner())`.

---

## 11. Final layout

```
sysdiag/
├─ .gitignore  requirements.txt
├─ schema.py rules.py data.py gpt.py train.py infer.py   # tiny GPT (identical to Windows)
├─ sysdiag.py history.py                                 # truth layer + logger
├─ context.py brain.py rag.py                            # Ollama chat brain + RAG (Linux-tuned prompt/path)
├─ art.py trends.py app.py chat.py                       # UI/CLI (identical to Windows)
├─ system_facts.md
├─ collectors/
│   └─ cpu.py mem.py disk.py gpu.py sensors.py net.py whea.py docker.py k3s.py usb.py storage.py
├─ corpus.txt   vocab.json   ckpt.pt   history.db   rag_index.db   # generated (ckpt/history/rag_index git-ignored)
```

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `(Ollama returned HTTP 400: cannot unmarshal array … into string)` | Gradio sent list-shaped content | `_text()` in `brain.py` — already included |
| Chat replies **one word** then stops | prompt filled `num_ctx`, no room to generate | keep retrieval lean (lower `TOP_K` / raise `MIN_SCORE` in `rag.py`); keep `num_ctx` ≥ prompt + reply |
| `(couldn't reach Ollama …)` | service down / model not pulled | `systemctl status ollama`, `ollama pull qwen2.5:32b` |
| `sensors: cpu_temp null` | lm-sensors not configured | `sudo sensors-detect --auto`; adjust chip names in `sensors.py` |
| `whea` always 0 | `journalctl -k` needs perms, or genuinely no MCEs | add user to `systemd-journal` group (0 is the healthy case) |
| `cuda False` | torch CPU build / driver | install the CUDA `torch` wheel matching `nvidia-smi` |
| `docker not found` / k3s error | not installed or no perms | optional collectors — ignore, or add user to `docker` group / allow passwordless `k3s kubectl` |
| Edited a file, app unchanged | Gradio cached the module | restart `app.py` |

---

## 13. Add a local RAG pipeline (semantic doc retrieval)

Everything above gives the chat brain a *live* picture of the machine (snapshot + findings) plus a
single static `system_facts.md`. **RAG** adds a *reference library*: point it at any Markdown docs —
homelab notes, hardware manuals, scraped wikis (PowerShell/Arch/Linux), runbooks — and the model
gets only the few paragraphs actually relevant to each question, pulled by semantic similarity,
instead of being fed (or not fed) a whole document by a keyword gate.

It stays true to the rest of Watch Tower: **local-only, read-only** (it only SELECTS text to show
the model), and degrades to silence if Ollama is down. It adds **one file** (`rag.py`), edits
**one** (`context.py`), and `brain.py` does **not** change. Run every command from the project
root (`sysdiag/`), where `rag.py` lives.

> Built to scale: this version embeds in **batches** and indexes **incrementally**, so a large
> corpus (tens of thousands of chunks) builds in minutes and editing one doc re-embeds only that
> doc. The mechanics are in **§13.6**.

### 13.1 Pull an embedding model

Retrieval needs a real *embedding* model (chat models like `qwen2.5:32b` return an empty vector
from the embeddings endpoint — they have no embedding head). The default is `nomic-embed-text`:

```bash
ollama pull nomic-embed-text
```
Expected (~274 MB, runs fine on CPU — no VRAM needed):
```
pulling manifest
pulling ... 100% ▕████████████████▏ 274 MB
verifying sha256 digest
success
```

US-built embedding models you can use instead (set `EMBED_MODEL` in `rag.py`):

| Embedder (US company) | `ollama pull` tag | Dim | Context | Size | Notes |
|---|---|---|---|---|---|
| nomic-embed-text (Nomic AI) | `nomic-embed-text` | 768 | 8192 | 274 MB | **default**; wants the `search_document:` / `search_query:` prefixes (already in `rag.py`) |
| snowflake-arctic-embed (Snowflake) | `snowflake-arctic-embed` · `:137m` · `:33m` | 1024 / 768 | 512 | 70–670 MB | strong English retrieval |
| snowflake-arctic-embed2 (Snowflake) | `snowflake-arctic-embed2` | 1024 | 8192 | 1.2 GB | multilingual + long context |
| granite-embedding (IBM) | `granite-embedding:30m` · `:278m` | 384 / 768 | 512 | 60 / 560 MB | enterprise |

> Non-US embedders you'll see in Ollama: `all-minilm` (sentence-transformers, Germany),
> `mxbai-embed-large` (Mixedbread, Germany) and `bge-*` (BAAI, China) — fine technically,
> excluded here as non-US. If you switch embedder, set
> `EMBED_MODEL`, adjust `DOC_PREFIX`/`QUERY_PREFIX` per its model card, and rebuild with
> `python rag.py --build --force`.

### 13.2 The vector store (sqlite-vec)

`rag.py` stores embeddings in **sqlite-vec** — a vector-search extension for the same SQLite you
already use for `history.db`. It's already in `requirements.txt`:

```bash
pip install sqlite-vec
```
sqlite-vec loads as a SQLite extension, which needs your Python's `sqlite3` built with extension
loading enabled. Confirm:
```bash
python -c "import sqlite3; sqlite3.connect(':memory:').enable_load_extension(True); print('OK')"
```
Expected: `OK`. (Most distro and python.org builds support it. A minimal/static build that raises
here would need `sqlite3` rebuilt with extension loading enabled.)

### 13.3 Create `rag.py`

Paste this into the project root. It is self-contained and self-tests with `python rag.py`. (The
listing is wrapped in a four-backtick fence because the code itself contains triple-backticks.)

````python
# rag.py — local RAG for Watch Tower. Makes your reference docs (homelab notes, hardware manuals,
# runbooks, scraped wikis) searchable so the chat model can quote the RIGHT few paragraphs instead
# of being fed a whole document. Embeddings come from Ollama's local embedding model; retrieval is
# a cosine KNN over a sqlite-vec vector store. READ-ONLY: it only SELECTS text to show the model.
#
# Scales to a LARGE corpus (tens of thousands of chunks) via two things:
#   * BATCH embedding   — many chunks per Ollama /api/embed call (falls back to /api/embeddings on
#                         older Ollama). Turns an hours-long sequential build into minutes.
#   * INCREMENTAL index — each source's content hash is stored; only NEW or CHANGED docs are
#                         re-embedded, and docs removed from SOURCES are dropped. Editing one small
#                         doc costs seconds, not a full re-embed of the whole corpus.
#
# Deps: Ollama (already required) + `ollama pull nomic-embed-text` + `pip install sqlite-vec`.
# Everything else (json/urllib/pathlib/hashlib/re/math/sqlite3) is stdlib.
#
# Build the index (do this once after adding docs; re-run anytime — it only does the delta):
#   python rag.py --build           # embed new/changed docs
#   python rag.py --build --force    # wipe + re-embed everything (after changing a tuning knob)

import json, urllib.request, urllib.error, pathlib, hashlib, re, math, sys, sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32

OLLAMA_HOST  = "http://127.0.0.1:11434"
OLLAMA_EMBED = OLLAMA_HOST + "/api/embed"        # batch endpoint (newer Ollama): {"input": [...]}
OLLAMA_EMB1  = OLLAMA_HOST + "/api/embeddings"   # single endpoint (older Ollama): {"prompt": "..."}
EMBED_MODEL  = "nomic-embed-text"                # `ollama pull nomic-embed-text` (~270 MB, CPU-ok)
EMBED_BATCH  = 64                                # chunks sent per /api/embed request
HERE = pathlib.Path(__file__).parent
DB   = HERE / "rag_index.db"                     # generated cache — git-ignored

# Docs to make searchable: EVERY *.md in this folder, plus the homelab notes (if present). Missing
# files are skipped. Drop a new .md in here and the next `python rag.py --build` picks it up.
SOURCES = [pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md", *sorted(HERE.glob("*.md"))]

# --- tuning knobs (the RAG equivalent of rules.THRESH — tune for YOUR docs) ---
CHUNK_CHARS = 1200    # size of each searchable slice (~300 tokens)
OVERLAP     = 200     # chars repeated between neighbours so a fact on a boundary isn't lost
TOP_K       = 4       # how many chunks to return per question
MIN_SCORE   = 0.45    # cosine floor; below this a chunk is "not really relevant" and is dropped
                      #   -> an off-topic question retrieves nothing. THIS is the knob to tune.

# nomic-embed-text wants these task prefixes; they materially improve retrieval. Other embedders
# differ: mxbai-embed-large wants only a query-side instruction and no document prefix. If unsure
# for your model, set both to "" — it works, just slightly weaker on the query side.
DOC_PREFIX   = "search_document: "
QUERY_PREFIX = "search_query: "


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)        # build progress -> stderr, never pollutes stdout


def _norm(v: list[float]) -> list[float]:
    """L2-normalize so cosine == dot product (lets sqlite-vec's L2 distance recover cosine)."""
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _embed(text: str, prefix: str = DOC_PREFIX) -> list[float]:
    """One text -> one normalized vector via the single-item endpoint (the fallback path)."""
    body = json.dumps({"model": EMBED_MODEL, "prompt": prefix + text}).encode()
    req = urllib.request.Request(OLLAMA_EMB1, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return _norm(json.loads(r.read())["embedding"])


def _embed_batch(texts: list[str], prefix: str = DOC_PREFIX) -> list[list[float]]:
    """Many texts -> many normalized vectors in ONE /api/embed call. Falls back to the older
    one-at-a-time /api/embeddings endpoint if this Ollama is too old to have /api/embed (HTTP 404)."""
    body = json.dumps({"model": EMBED_MODEL, "input": [prefix + t for t in texts]}).encode()
    req = urllib.request.Request(OLLAMA_EMBED, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return [_norm(v) for v in json.loads(r.read())["embeddings"]]
    except urllib.error.HTTPError as e:
        if e.code == 404:                          # old Ollama without /api/embed -> single calls
            return [_embed(t, prefix) for t in texts]
        raise


def _embed_all(texts: list[str], prefix: str = DOC_PREFIX) -> list[list[float]]:
    """Embed a whole doc's chunks in EMBED_BATCH-sized requests."""
    out = []
    for i in range(0, len(texts), EMBED_BATCH):
        out.extend(_embed_batch(texts[i:i + EMBED_BATCH], prefix))
    return out


def _chunk(text: str) -> list[str]:
    """Markdown-heading-aware AND code-fence-aware: start a new chunk at each '#'-heading, but
    NOT at '#' lines inside ``` / ~~~ code fences (shell/YAML examples are full of '# comments',
    which would otherwise shred code blocks). Keeps tables / spec lists / code examples whole.
    Oversized sections fall back to the sliding window; tiny adjacent sections are packed together."""
    heading = re.compile(r"^#{1,6}\s")
    fence = re.compile(r"^\s*(```|~~~)")
    sections, cur, in_fence = [], [], False
    for line in text.splitlines():
        if fence.match(line):
            in_fence = not in_fence                    # toggle: a fence delimiter is never a heading
        elif heading.match(line) and not in_fence and cur:
            sections.append("\n".join(cur)); cur = []  # real heading outside code -> new section
        cur.append(line)
    if cur:
        sections.append("\n".join(cur))
    sections = [s.strip() for s in sections if s.strip()]
    step = CHUNK_CHARS - OVERLAP
    chunks, buf = [], ""
    for sec in sections:
        if len(sec) > CHUNK_CHARS:                    # oversized section -> window it
            if buf:
                chunks.append(buf); buf = ""
            chunks += [sec[i:i + CHUNK_CHARS] for i in range(0, len(sec), step)]
        elif len(buf) + len(sec) + 2 <= CHUNK_CHARS:  # pack small sections together
            buf = f"{buf}\n\n{sec}" if buf else sec
        else:                                         # buf full -> flush, start a new one
            chunks.append(buf); buf = sec
    if buf:
        chunks.append(buf)
    return chunks or [text]


def _load_sources() -> list[tuple[str, str, str]]:
    """[(name, text, sha256), ...] de-duplicated by resolved path; missing files skipped."""
    docs, seen = [], set()
    for p in SOURCES:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp in seen:
            continue
        seen.add(rp)
        try:
            t = p.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue                          # missing file: skip, exactly like context.py
        if t:
            sha = hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()
            docs.append((p.name, t, sha))
    return docs


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.enable_load_extension(True)
    sqlite_vec.load(con)              # the vec0 extension is per-connection
    con.enable_load_extension(False)
    return con


def _ensure_schema(con) -> None:
    con.executescript(
        "CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, source TEXT, text TEXT);"
        "CREATE TABLE IF NOT EXISTS sources(name TEXT PRIMARY KEY, sha TEXT);"
        "CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);"
    )


def _meta_get(con, key: str) -> "str | None":
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def _meta_set(con, key: str, value: str) -> None:
    con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))


def _ensure_vec_table(con, dim: int) -> None:
    """Create the vec0 table on first use; its dimension is fixed at creation, recorded in meta."""
    if _meta_get(con, "dim") is None:
        con.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{dim}])")
        _meta_set(con, "dim", str(dim))


def _delete_source(con, name: str) -> None:
    """Drop a doc's chunks + vectors (vec table may not exist yet on a first build)."""
    try:
        con.execute("DELETE FROM vec_chunks WHERE rowid IN (SELECT id FROM chunks WHERE source=?)",
                    (name,))
    except sqlite3.OperationalError:
        pass                              # vec_chunks not created yet
    con.execute("DELETE FROM chunks WHERE source=?", (name,))
    con.execute("DELETE FROM sources WHERE name=?", (name,))


def build_index(force: bool = False) -> sqlite3.Connection:
    """Embed every NEW or CHANGED source into a sqlite-vec table, cached in rag_index.db. Only the
    delta is re-embedded (per-source content hash); removed docs are dropped. Returns an OPEN
    connection with the extension loaded. `force=True` wipes and re-embeds the whole corpus."""
    docs = _load_sources()
    con = _connect()
    _ensure_schema(con)
    settings = f"{CHUNK_CHARS}|{OVERLAP}|{EMBED_MODEL}|{DOC_PREFIX}|{QUERY_PREFIX}"
    if force or _meta_get(con, "settings") != settings:
        # a settings change invalidates every stored embedding -> wipe and full rebuild
        con.executescript("DROP TABLE IF EXISTS vec_chunks;"
                           "DELETE FROM chunks; DELETE FROM sources; DELETE FROM meta;")
        _ensure_schema(con)
        _meta_set(con, "settings", settings)
    have = dict(con.execute("SELECT name, sha FROM sources").fetchall())
    current = {name: (text, sha) for name, text, sha in docs}
    for name in set(have) - set(current):          # docs removed from SOURCES
        _delete_source(con, name); _log(f"  [removed] {name}")
    todo = [(n, t, s) for n, (t, s) in current.items() if have.get(n) != s]
    if not todo:
        con.commit()
        return con                                 # nothing new/changed -> reuse the embeddings
    _log(f"indexing {len(todo)} new/changed doc(s) of {len(current)} (batch={EMBED_BATCH})...")
    for name, text, sha in todo:
        _delete_source(con, name)                  # clear stale rows if the doc changed
        chunks = _chunk(text)
        if not chunks:
            continue
        vecs = _embed_all(chunks)
        _ensure_vec_table(con, len(vecs[0]))
        for txt, v in zip(chunks, vecs):
            cur = con.execute("INSERT INTO chunks(source, text) VALUES(?, ?)", (name, txt))
            con.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES(?, ?)",
                        (cur.lastrowid, serialize_float32(v)))
        con.execute("INSERT OR REPLACE INTO sources(name, sha) VALUES(?, ?)", (name, sha))
        con.commit()                               # commit per doc -> safe to interrupt and resume
        _log(f"  [indexed] {name}: {len(chunks)} chunks")
    return con


def _knn(con, question: str, k: int):
    """The k nearest chunks as [(cosine_score, source, text), ...]; empty if the corpus is empty."""
    q = serialize_float32(_embed(question, QUERY_PREFIX))
    try:
        rows = con.execute(
            "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (q, k),
        ).fetchall()
    except sqlite3.OperationalError:
        return []                    # no vec_chunks table -> nothing indexed
    out = []
    for rowid, dist in rows:
        score = 1.0 - (dist * dist) / 2.0    # L2 on UNIT vectors -> cosine (vectors are normalized)
        src, txt = con.execute("SELECT source, text FROM chunks WHERE id = ?", (rowid,)).fetchone()
        out.append((score, src, txt))
    return out


def retrieve(question: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[str]:
    """Up to k reference chunks relevant to the question. Empty if nothing clears min_score."""
    con = build_index()
    hits = _knn(con, question, k)
    con.close()
    return [f"[{src}] {txt}" for score, src, txt in hits if score >= min_score]


def context_block(question: str) -> str:
    """Ready-to-inject grounding text for context.build(); '' when nothing is relevant.
    NEVER raises: if Ollama is down or the embed model isn't pulled, retrieval degrades to ''
    so the chat keeps working (static facts + live snapshot + findings still ground the answer).
    This is what lets context.build() — called OUTSIDE brain.ask's try/except — stay crash-proof."""
    try:
        hits = retrieve(question)
    except Exception:
        return ""                              # Ollama unavailable / model not pulled -> no docs
    if not hits:
        return ""
    return ("REFERENCE DOCS (retrieved as most relevant to this question — quote these):\n\n"
            + "\n\n---\n\n".join(hits))


def _scored(question: str):
    """All chunks scored, nearest first — for `--scores` calibration."""
    con = build_index()
    n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
    hits = _knn(con, question, n or 1)
    con.close()
    return hits


def demo():  # the one runnable check
    assert len(_chunk("x" * 3000)) >= 3, "sliding-window chunker is wrong"
    v = [0.6, 0.8]                             # a unit vector's cosine with itself must be 1
    assert abs(sum(a * b for a, b in zip(v, v)) - 1.0) < 1e-6, "cosine math wrong"
    print("rag chunk/math ok")
    if not DB.exists():                        # honor "build later": don't kick off a full build here
        print(f"(index not built yet — run `python rag.py --build` to embed {len(_load_sources())} docs)")
        return
    try:
        con = _connect(); n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]; con.close()
        if not n:
            print("(index is empty — run `python rag.py --build`)"); return
        hits = retrieve("how is my reverse proxy / homelab networking set up?")
        print(f"rag index ok: {n} chunks; query returned {len(hits)} relevant chunk(s)")
        if hits:
            print("top hit:", hits[0][:160].replace("\n", " "))
    except Exception as e:
        print(f"(skipped live retrieve - is Ollama up + `ollama pull {EMBED_MODEL}` done? {e})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        con = build_index(force="--force" in sys.argv)
        n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]; con.close()
        print(f"index built: {n} chunks from {len(_load_sources())} doc(s)")
    elif len(sys.argv) > 2 and sys.argv[1] == "--scores":
        for score, src, txt in _scored(sys.argv[2]):
            print(f"{score:.3f}  [{src}] {txt[:90].strip()}")
    else:
        demo()
````

Drop any `.md` you want searchable into the project folder — `SOURCES` globs every `*.md` in it
automatically, plus your homelab notes. Offline self-test (no Ollama needed for the asserts):

```bash
python rag.py
```
Expected before you've built the index:
```
rag chunk/math ok
(index not built yet — run `python rag.py --build` to embed 20 docs)
```

### 13.4 Wire it into `context.py`

`context.build(message)` already produces the `{ctx}` string in `brain.SYSTEM`. RAG replaces the
old keyword gate (`_wants_homelab` / whole-doc dump) with semantic retrieval.

**13.4a** — add the import at the top of `context.py`:
```python
import json, pathlib
import rules
import rag                      # NEW
```
**13.4b** — append retrieved chunks at the end of `build()`:
```python
def build(message: str = "") -> str:
    snap, findings = snapshot_and_findings()
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        "LIVE SNAPSHOT (JSON, just collected):",
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    refs = rag.context_block(message)      # semantic retrieval replaces the keyword gate
    if refs:
        parts += ["", refs]
    return "\n".join(parts)
```
**13.4c** — delete the now-dead keyword gate (`HOMELAB`, `HOMELAB_TRIGGERS`, `_wants_homelab`) and
move that doc path into `rag.SOURCES` (it's already covered by the `*.md` glob if the doc lives in
the project folder). Update the `__main__` self-test:
```python
if __name__ == "__main__":
    out = build("how is my reverse proxy set up?")
    assert "FINDINGS" in out, "context block lost its findings"
    print(out[:800])
```
`brain.py` is unchanged — it calls `context.build(user_text)` and passes the whole grounded string
as the system prompt.

### 13.5 Build the index

From the project root (`sysdiag/`), with Ollama running and `nomic-embed-text` pulled:

```bash
python rag.py --build
```
Expected (counts depend on your docs; the big scraped corpora dominate):
```
indexing 20 new/changed doc(s) of 20 (batch=64)...
  [indexed] HOMELAB-COMPLETE-SETUP.md: 37 chunks
  [indexed] Docker-Troubleshooting.md: 290 chunks
  [indexed] arch-wiki-merged.md: 21044 chunks
  [indexed] powershell-docs-merged.md: 28850 chunks
  ...
index built: 54213 chunks from 20 doc(s)
```
- It commits **per document**, so a long first build is safe to Ctrl+C and resume — re-running
  `--build` continues where it left off.
- A multi-MB corpus (e.g. the merged PowerShell/Arch/Linux wikis) is **tens of thousands of
  chunks**. On a GPU that Ollama can use for the embedder, that's minutes; on CPU, longer (let it
  run). After the first build it's instant unless a doc changes.
- Re-run `python rag.py --build` after editing or adding any doc — only the changed/new docs
  re-embed (see §13.6). Use `--build --force` only after changing `CHUNK_CHARS`/`OVERLAP`/the
  embedder, which invalidates every stored vector.

### 13.6 How it scales to a large corpus (batch + incremental)

Two design choices make a 60 MB+ corpus practical:

1. **Batch embedding.** `_embed_all` posts up to `EMBED_BATCH` (64) chunks per `/api/embed` call
   instead of one HTTP round-trip per chunk. On a large corpus that's the difference between
   minutes and hours. If your Ollama predates `/api/embed`, `_embed_batch` catches the 404 and
   transparently falls back to the one-at-a-time `/api/embeddings` endpoint.

2. **Incremental indexing.** Each source's SHA-256 is stored in a `sources` table. On every build,
   `rag.py` compares hashes and re-embeds **only** new or changed docs; docs you removed from
   `SOURCES` are deleted from the index. So editing one small note re-embeds seconds of work, not
   the whole corpus — and the per-document commit makes the build resumable.

The store is **sqlite-vec**, whose KNN runs in the DB engine, so ~50k+ vectors stay fast. Retrieval
always returns just `TOP_K` chunks, so corpus size never bloats the chat context — a bigger library
only improves recall. (Both behaviors are covered by the `python rag.py` self-tests and a small
incremental-logic check.)

### 13.7 Verify end to end

```bash
python context.py
```
A homelab/manual-style question pulls a `REFERENCE DOCS (...)` section into the printed block; a
pure-hardware question (e.g. "is my GPU hot?") won't.

Calibrate the relevance floor — `--scores` prints every chunk's cosine so you can pick `MIN_SCORE`:
```bash
python rag.py --scores "what ports do I have on my motherboard?"
```
```
0.71  [MAG_Z790_TOMAHAWK_MAX_WIFI_User_Guide.md] ## Rear I/O ...
0.68  [MAG_Z790_TOMAHAWK_MAX_WIFI_User_Guide.md] ### USB connectors ...
0.39  [Docker-Troubleshooting.md] ## Networking ...
```
Then use the chat as normal — it cites the retrieved text instead of guessing:
```bash
python chat.py        # or: python app.py
```

### 13.8 Tuning & maintenance

| Knob (in `rag.py`) | Default | Change it when |
|---|---|---|
| `SOURCES` | every `*.md` in the folder + homelab doc | it's a glob — just drop a `.md` in the folder |
| `MIN_SCORE` | `0.45` | **the main dial.** Higher = stricter (less noise); lower = looser (more recall) |
| `TOP_K` | `4` | answers need more context; watch you don't blow `num_ctx` in `brain.py` |
| `CHUNK_CHARS` / `OVERLAP` | `1200` / `200` | smaller = finer retrieval; bigger = more context per hit |
| `EMBED_MODEL` | `nomic-embed-text` | switching embedder (adjust the prefixes; `--build --force`) |
| `EMBED_BATCH` | `64` | lower if Ollama OOMs on a batch; higher to squeeze a fast GPU |

Git-ignore the cache (already in this project's `.gitignore`):
```
rag_index.db
```

### 13.9 Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `HTTP Error 404` on embed | embed model not pulled — `ollama pull nomic-embed-text`; check `ollama list` |
| retrieval always empty | you pointed `EMBED_MODEL` at a **chat** model (empty vectors). Use a real embedder |
| nothing retrieved for a relevant question | `MIN_SCORE` too high, or the doc isn't in the folder. Use `python rag.py --scores "..."` |
| off-topic questions still pull chunks | `MIN_SCORE` too low — raise it |
| first build is slow | expected on a big corpus; it batches + commits per doc, so it's resumable |
| edited a doc, answer unchanged | rebuild: `python rag.py --build` (only that doc re-embeds) |
| `OperationalError` on `enable_load_extension` | your Python can't load SQLite extensions — rebuild `sqlite3` with them enabled |
