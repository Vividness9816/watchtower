from __future__ import annotations
import json
import math
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.nn import functional as F

from schema import EOS  # document separator / end-of-sequence marker


# =================================================================== tokenizer
class CharTokenizer:
    """The simplest honest tokenizer: one integer per character. Fully transparent -
    you can see exactly how text becomes the integers the model consumes. (Upgrade to
    BPE later; see README.) Always includes EOS in the vocab."""

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


# =================================================================== config
@dataclass
class GPTConfig:
    vocab_size: int = 128
    block_size: int = 256   # max context the model can attend over
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384       # must be divisible by n_head
    dropout: float = 0.1
    bias: bool = True       # bias in Linear/LayerNorm


# =================================================================== attention
class CausalSelfAttention(nn.Module):
    """Multi-head self-attention with a causal mask so position t can only attend to
    positions <= t. This is the only place tokens exchange information."""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head = cfg.n_head
        self.n_embd = cfg.n_embd
        # one matmul produces q, k, v together: (C) -> (3C)
        self.c_attn = nn.Linear(cfg.n_embd, 3 * cfg.n_embd, bias=cfg.bias)
        self.c_proj = nn.Linear(cfg.n_embd, cfg.n_embd, bias=cfg.bias)
        self.attn_dropout = nn.Dropout(cfg.dropout)
        self.resid_dropout = nn.Dropout(cfg.dropout)
        # lower-triangular causal mask, registered as a buffer (moves with .to(device),
        # not a learnable parameter). Shape (1,1,block,block) to broadcast over B and nh.
        self.register_buffer(
            "tril",
            torch.tril(torch.ones(cfg.block_size, cfg.block_size)).view(1, 1, cfg.block_size, cfg.block_size),
        )

    def forward(self, x):                       # x: (B, T, C)
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)   # each (B, T, C)
        hs = C // self.n_head
        # split C into (nh, hs) and move heads to the batch-like dim -> (B, nh, T, hs)
        q = q.view(B, T, self.n_head, hs).transpose(1, 2)
        k = k.view(B, T, self.n_head, hs).transpose(1, 2)
        v = v.view(B, T, self.n_head, hs).transpose(1, 2)
        # attention scores: (B,nh,T,hs) @ (B,nh,hs,T) -> (B,nh,T,T)
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(hs))
        att = att.masked_fill(self.tril[:, :, :T, :T] == 0, float("-inf"))  # causal
        att = F.softmax(att, dim=-1)
        att = self.attn_dropout(att)
        y = att @ v                              # (B,nh,T,T) @ (B,nh,T,hs) -> (B,nh,T,hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C)     # reassemble heads -> (B,T,C)
        return self.resid_dropout(self.c_proj(y))


class MLP(nn.Module):
    """Position-wise feed-forward: expand 4x, GELU, project back."""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.c_fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd, bias=cfg.bias)
        self.c_proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd, bias=cfg.bias)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x):
        return self.dropout(self.c_proj(F.gelu(self.c_fc(x))))


class Block(nn.Module):
    """Pre-norm residual block: x = x + attn(ln(x)); x = x + mlp(ln(x))."""

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


# =================================================================== full model
class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.n_embd)   # (V, C)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.n_embd)   # (block, C)
        self.drop = nn.Dropout(cfg.dropout)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd, bias=cfg.bias)
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)  # (C, V)
        # weight tying: input embedding and output projection share weights (GPT-2 trick,
        # fewer params, usually better).
        self.tok_emb.weight = self.lm_head.weight
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def num_params(self) -> int:
        # subtract tied head so we don't double-count
        return sum(p.numel() for p in self.parameters()) - self.lm_head.weight.numel()

    def forward(self, idx, targets=None):       # idx: (B, T) longs
        B, T = idx.shape
        assert T <= self.cfg.block_size, f"sequence {T} > block_size {self.cfg.block_size}"
        pos = torch.arange(T, device=idx.device)                 # (T,)
        x = self.tok_emb(idx) + self.pos_emb(pos)                # (B,T,C) + (T,C) broadcast
        x = self.drop(x)
        for blk in self.blocks:
            x = blk(x)
        x = self.ln_f(x)
        logits = self.lm_head(x)                                 # (B, T, V)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-1
            )
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8, top_k=None, eos_id=None):
        """Autoregressive sampling. idx: (B,T) seed. Stops early if B==1 and eos_id emitted."""
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size:]             # crop to context window
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / max(temperature, 1e-6)   # last step -> (B,V)
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")
            probs = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(probs, num_samples=1)        # (B,1)
            idx = torch.cat((idx, nxt), dim=1)
            if eos_id is not None and idx.size(0) == 1 and nxt.item() == eos_id:
                break
        return idx