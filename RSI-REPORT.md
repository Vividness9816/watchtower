# Watch Tower — RSI Test Report

A rigorous recursive-self-improvement (RSI) cycle against Watch Tower. **Method:** build a
frozen, deterministic exam (see `exam/FROZEN.md`), measure a run-0 baseline, then each run applies
verified improvements, re-scores against the *same* frozen exam, and keeps the change only if the
composite rises. Stop at 20 runs, or after 4 consecutive runs with no gain.

Every dimension is scored by machine, not vibes: rule ground-truth, held-out narration F1,
retrieval MRR, seeded deterministic brain assertions, latency budgets, and feature contracts.
The exam is frozen by SHA256 manifest so no run can weaken the questions to inflate a score.

## Environment

- Windows 11, i9-14900K, RTX 5090 32 GB, 64 GB DDR5; LibreHardwareMonitor web server up (:8085);
  Docker Desktop (44 containers) + k3s in WSL Ubuntu; Ollama (`qwen2.5:32b`, `hermes3`,
  `nomic-embed-text`, `mxbai-embed-large`).
- Python 3.14 venv (`torch 2.11+cu128`, `gradio 6.19`, `pandas`, `sqlite-vec`).

## Scoreboard

| Run | S1 cov | S2 rules | S3 narr | S4 retr | S5 brain | S6 flow | S7 feat | **Composite** | Δ |
|-----|--------|----------|---------|---------|----------|---------|---------|---------------|---|
| 0 (baseline) | 0.5063 | 0.6939 | 0.9931 | 0.7737 | 1.0000 | 0.6923 | 0.2222 | **0.7086** | — |

## Per-run findings

### Run 0 — baseline + frozen exam

Built the seven-dimension frozen exam and measured the untouched repo. Key facts established:

- **Full train pipeline is deterministic** at the artifact level: `data.py 8000` reproduces
  `corpus.txt` byte-for-byte (2,015,944 chars, 61 unique chars); `train.py` reproduces
  `vocab.json`. Trained `ckpt.pt` reaches val loss 0.2326; `infer.py --demo` narrates a held-out
  snapshot correctly.
- **Baseline composite 0.7086.** S3 narration (0.9931) and S5 brain (1.0 on 13 frozen
  deterministic cases including prompt-injection and absent-data canaries) start near ceiling.
  S1/S2/S6/S7 carry the headroom the RSI loop will close.

The run-0 audit (8-agent adversarial workflow, ~869k tokens) surfaced the backlog the following
runs draw from — findings are recorded per run as they're fixed and re-verified.

**First fix shipped in run 0:** `rag_index.db` (which embeds homelab-doc chunks) was **not**
gitignored — a trailing inline comment on its `.gitignore` line made git treat the whole line as
one literal pattern. One `git add -A` from committing private data. Fixed + pushed (`fe6ec9a`).
