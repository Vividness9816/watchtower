# Watch Tower

**A local, read-only PC health dashboard with a built-from-scratch GPT and a local LLM chat — no cloud, no API keys, no telemetry.**

![platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![llm](https://img.shields.io/badge/LLM-Ollama%20qwen2.5%3A32b-green)
![status](https://img.shields.io/badge/release-v1.0-brightgreen)
![privacy](https://img.shields.io/badge/network-127.0.0.1%20only-orange)

Watch Tower reads your machine's real sensors (CPU/GPU/RAM/disk/temps/Docker/…), turns them into
plain-language health reports, and lets you *ask* about your hardware in a chat that's grounded in
the live numbers. Everything runs on `127.0.0.1`. The model only **advises** — nothing it says is
ever executed.

---

## Two AIs, both local

| | What | Size | Needs |
|---|---|---|---|
| **Tiny GPT** | A char-level transformer **you train from scratch** on synthetic snapshots. Writes a one-paragraph health report from a metrics line. | ~10 MB (`ckpt.pt`) | nothing — fully offline |
| **Chat brain** | **Ollama** running `qwen2.5:32b`, grounded in the live snapshot + rule-engine findings. Answers free-form questions with copy-pasteable fix steps. | ~19 GB download | a CUDA GPU (32 GB ideal) |

They're independent — run either, both, or neither.

---

## Architecture

```
collectors/*.py ──► sysdiag.py ──► snapshot{json} ──► rules.py ──► findings[]
                                      │
        ┌──────────────────────────────┼───────────────────────────────┐
        ▼                              ▼                               ▼
 schema.serialize ─► tiny GPT     context.build ─► brain.ask ─► Ollama qwen2.5:32b
 (train.py / infer.py)             (chat.py CLI  +  app.py web UI + history graph)
```

- **Truth layer** — each `collectors/*.py` script prints one JSON object; `sysdiag.py` runs them
  all and merges the result; `rules.py` turns it into severity-ranked findings. A failing collector
  degrades to `{"error": …}` instead of crashing the app.
- **Tiny GPT** — `schema.py` defines the exact metrics format; `data.py` synthesizes a training
  corpus; `gpt.py` is the transformer; `train.py` trains it; `infer.py` runs it.
- **Chat brain** — `context.py` assembles the grounding context (static facts + live snapshot +
  findings, with an optional homelab doc gated behind keywords); `brain.py` calls Ollama.
- **UI** — `app.py` (Gradio web dashboard: live panel, chat, history graph) and `chat.py` (CLI).
  `history.py` logs a snapshot to SQLite on a timer; `trends.py` reads it for the graph.

---

## Features

- 🔎 **Live findings** — thresholds per metric (`rules.py`), CPU/GPU temp, RAM, disk, WHEA/MCE
  hardware errors, stalled-fan + hot rule, internet-down.
- 🧠 **From-scratch GPT** — a complete, readable ~10 M-param transformer (tokenizer → attention →
  training loop → sampling) trained offline in minutes. Great for learning how GPTs work.
- 💬 **Grounded chat** — a 32B model that cites your actual numbers and never invents readings;
  told it can only advise, never act.
- 📊 **History graph** — select by recent runs, hover any point for its date + time.
- 🖥️ **Cross-platform** — Windows (PowerShell/CIM/WHEA collectors) and Linux
  (psutil/lm-sensors/MCE collectors).
- 🔒 **Local-only** — binds `127.0.0.1`; no API keys, no env vars, no outbound calls (Ollama is
  local too). Auto-frees the model's VRAM on exit.

---

## Requirements

- **Python 3.10+** (built on 3.14)
- **NVIDIA GPU + driver** (`nvidia-smi`) — required to train the GPT fast and to run the 32B chat
  model usefully. CPU-only works for everything except a snappy 32B chat.
- **[Ollama](https://ollama.com)** — for the chat brain
- **CPU-temp source:** Windows → [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
  web server (port 8085); Linux → `lm-sensors`
- *(optional)* **Docker** for the `docker`/`k3s` collectors

Python deps (only three; everything else is stdlib): `torch`, `gradio`, `pandas` (+ `psutil` on Linux).

---

## Quick start

Full, copy-paste, step-by-step guides with expected output for every command:

- **Windows:** [`docs/RECREATE-WINDOWS.md`](docs/RECREATE-WINDOWS.md)
- **Linux:** [`docs/RECREATE-LINUX.md`](docs/RECREATE-LINUX.md)

The short version:

```bash
# 1. venv + deps  (Windows: python -m venv .venv ; .\.venv\Scripts\Activate.ps1)
python -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu128   # match your CUDA
pip install gradio pandas         # + psutil on Linux

# 2. build & train the tiny GPT (writes ckpt.pt + vocab.json)
python data.py 8000
python train.py

# 3. pull the chat model
ollama pull qwen2.5:32b

# 4. run it
python app.py        # web dashboard at http://127.0.0.1:7860
python chat.py       # or the CLI
```

---

## Usage

| Command | What it does |
|---|---|
| `python sysdiag.py` | print live findings |
| `python sysdiag.py diag --json` | full live snapshot as JSON |
| `python sysdiag.py report` | tiny-GPT narration of the live snapshot |
| `python data.py 8000` | (re)generate `corpus.txt` (8000 synthetic docs) |
| `python train.py` | train the GPT → `ckpt.pt` + `vocab.json` |
| `python infer.py --demo` | show INPUT / rule-truth / model-output for a random snapshot |
| `python history.py` | log one snapshot to `history.db` (run on a timer) |
| `python chat.py` | CLI chat |
| `python app.py` | Gradio web dashboard |

Each pure-logic module self-tests: `python schema.py`, `python rules.py`,
`python collectors/docker.py --test` → `… ok`.

---

## Configuration

No env vars, no secrets. Tune these in source:

- **`rules.py` → `THRESH`** — warn/crit thresholds per metric. *Tune for your silicon.*
- **`brain.py`** — `MODEL` (any model you've `ollama pull`ed), `num_ctx` (context window; 32768
  fits a 32 GB GPU — ~8 GB KV cache; drop to 16384/8192 on smaller GPUs), `keep_alive` (how long
  the model stays in VRAM).
- **`system_facts.md`** — static facts about your machine the chat model reads (CPU/GPU model,
  normal temps, what you care about). *Edit for your box.*
- **`context.py` → `HOMELAB`** — optional path to a homelab doc; injected only when the question
  is homelab-related (keyword-gated). Missing file is silently skipped.

---

## Project layout

```
schema.py rules.py data.py gpt.py train.py infer.py   # tiny GPT
sysdiag.py history.py                                  # truth layer + logger
context.py brain.py                                    # Ollama chat brain
art.py trends.py app.py chat.py                        # UI / CLI
system_facts.md  requirements.txt  .gitignore
collectors/   cpu mem disk gpu sensors net docker k3s whea tpm me usb storage  (.py)
docs/         RECREATE-WINDOWS.md  RECREATE-LINUX.md
# generated (git-ignored): corpus.txt* vocab.json ckpt.pt history.db   (*corpus is deterministic)
```

> **Linux note:** the Linux release swaps the PowerShell collectors for
> psutil/lm-sensors/MCE equivalents and omits the Windows-only `tpm`/`me` collectors. The shared
> `schema.py`/model are identical; the Linux `disk` collector aliases root `/` to the key `C` so
> the trained model's `disk_C` input stays populated. See `docs/RECREATE-LINUX.md`.

---

## Privacy & safety

- **Read-only.** The model is instructed to *advise only*; its output is text shown to a human and
  is **never executed**.
- **Local-only.** Binds `127.0.0.1:7860`; Ollama runs locally; no API keys, no outbound network.
- **VRAM hygiene.** `app.py`/`chat.py` run `ollama stop` on clean exit to free the GPU.

---

## License

Personal project. No warranty. Use at your own risk.
