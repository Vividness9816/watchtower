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
- *(optional)* **Add local RAG to the chat:** [`docs/ADD-RAG.md`](docs/ADD-RAG.md) — semantic
  retrieval over your own reference docs, zero new pip deps (one `ollama pull`)

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
sysdiag.py history.py discover.py                      # truth layer + logger + bus discovery
context.py brain.py                                    # Ollama chat brain
art.py trends.py live.py app.py chat.py                # UI / CLI + live sampler
system_facts.md  requirements.txt  .gitignore
collectors/   cpu mem disk gpu sensors net docker k3s whea tpm me usb storage
              lights power vm services ssh             # RGB + boot forensics + Hyper-V + systemd + remote-VM SSH
              sdr rx tx tuner antenna  _sdr_common     # SDR/antenna skeletons (fill when hardware lands)
docs/         RECREATE-WINDOWS.md  RECREATE-LINUX.md
# generated (git-ignored): corpus.txt* vocab.json ckpt.pt history.db   (*corpus is deterministic)
```

**Deep sensors.** `sensors.py` reads LibreHardwareMonitor's whole tree (every temp — CPU/VRM/
chipset/NVMe/GPU-hotspot — every fan **and pump** RPM, AIO **liquid temp**), with a `liquidctl`
fallback for the AIO when LHM is down (note: NZXT CAM holds the Kraken's HID exclusively — close
CAM or run LHM). `gpu.py` adds decoded throttle reasons, PCIe link gen/width current-vs-max,
fan %, P-state and clocks. `power.py` counts Kernel-Power 41 / 6008 / throttle events — the
software-visible shadow of the board's debug LEDs (which are POST-time hardware and unreadable).
`lights.py` reads actual RGB zone state through the OpenRGB SDK server.

**Live sampling.** `live.py` runs a background sampler inside the app: cheap collectors
(cpu/gpu/mem/sensors/disk) every 5s, the full fleet every 60s, kept in a ~1h in-memory ring.
The dashboard's stats panel, the **Live graphs** section (multi-select metrics, 5/15/60-min
window, 5s refresh; full-fleet metrics like net/whea plot at their real 60s cadence) and the
chat brain all read this cache — a chat message normally costs zero collector runs (it falls
back to a one-shot snapshot only if the cache is stale) and the LLM context carries the
snapshot with per-tier age stamps plus a `RECENT TRENDS` digest of the last 10 minutes.
Long-term history stays with `history.py`/Task Scheduler and the History graphs.

**Remote monitoring (one machine watches another).** Collectors must run on the monitored
box; the GUI/rules/chat run on the monitoring box; the NanoGPT narrator can sit on either.
The agent side is stdlib-only: copy `collectors/ sysdiag.py ship.py` to the monitored
machine and run

```
# on the MONITORED machine (agent) — add --narrate to ship NanoGPT reports too
set WATCHTOWER_SHIP_URL=http://<nifi-or-gui-host>:8081/watchtower
set WATCHTOWER_TOKEN=<shared-secret>
set WATCHTOWER_HOST=lab-pc        # optional: identity in the payload (default: this machine's name)
python ship.py

# on the MONITORING machine (GUI)
set WATCHTOWER_REMOTE=1
set WATCHTOWER_TOKEN=<shared-secret>
set WATCHTOWER_INGEST_BIND=0.0.0.0:7861   # optional: receiver bind (default). Use 127.0.0.1:7861
python app.py                             #   if NiFi runs on the same box and nothing else should reach it
```

**Per-machine config & identity — `ship.config.json`.** Copy `ship.config.example.json`
to `ship.config.json` on each monitored box (or point `WATCHTOWER_SHIP_CONFIG` at one).
This is where you shape the shipped JSON and, crucially, **name the reporter** so the GUI can
tell your machines apart:

```jsonc
{
  "host":  "lab-pc-01",                       // identity — how the GUI names/selects this box
  "label": "Lab PC — rack 2, GPU node",       // friendly display label
  "tags":  { "location": "basement", "role": "gpu-node" },   // free-form, shown on the panel
  "fast":  ["cpu", "gpu", "mem", "sensors", "disk"],  // collectors in the 5s tier
  "full":  null,                              // 60s tier: null = the whole fleet, or a list
  "fast_seconds": 5, "full_seconds": 60, "narrate": false,
  "url":   "http://nifi-or-gui-host:8081/watchtower"
}
```

The identity and destination are env-overridable (env wins) — `WATCHTOWER_HOST` for `host`,
`WATCHTOWER_SHIP_URL` for `url` — so **one shared config file** plus a per-host
`WATCHTOWER_HOST=...` on the command line is enough to vary which machine is reporting and
where it ships. The other keys (label/tags/tiers/cadence) come from the file.

**Multiple machines, one dashboard.** Each distinct `host` gets its **own** ring, snapshot,
and findings — no cross-contamination. The GUI's **Host** selector (top of the page) lists
every machine reporting in; pick one and the stats panel, live graphs, and chat all switch to
it (the chat answers about the selected host, with that host's findings). New agents appear in
the selector live. `ship.py` streams JSON on the two-tier cadence (fast 5s `{"partial": true}`,
full fleet 60s); the receiver (`/ingest`, default `0.0.0.0:7861`, token required or it refuses
to start) feeds those per-host rings — a stale feed is flagged `STALE` rather than ever
sampling the monitoring machine. Point `WATCHTOWER_SHIP_URL` directly at
`http://<gui-host>:7861/ingest` for the no-middleman setup, or route through **Apache NiFi**
for buffering/provenance/fan-out — the minimal flow is two processors:

| processor | properties |
|---|---|
| `ListenHTTP` | Listening Port `8081`, Base Path `watchtower`, HTTP Headers to receive as Attributes `X-Watchtower-Token` |
| `InvokeHTTP` | HTTP Method `POST`, URL `http://<gui-host>:7861/ingest`, Request Content-Type `application/json`, Attributes to Send `X-Watchtower-Token` |

Connect `ListenHTTP success -> InvokeHTTP`; NiFi's queue then absorbs GUI downtime
(back-pressure + retry), records provenance per snapshot, and can tee the same stream to
disk/Grafana/alerts with additional processors.

**Bus discovery.** `python sysdiag.py discover` scans USB/PCI (PnP) + COM ports and maps known
devices (SDRs, AIOs, RGB) to the collector that should cover them; add `--spawn` to write a stub
collector for a recognized device that has none — the snapshot glob picks it up automatically.
The SDR skeletons (`sdr/rx/tx/tuner/antenna.py`) run today and emit `present:false`; their
`FILL-ME` blocks document the intended probes to complete when hardware arrives — `antenna.py`
covers the selected antenna port, its options, RSSI, and (where a TX-capable chain with a
return-loss bridge exposes it) SWR.

**Remote Linux VMs over SSH.** `ssh.py` scrapes components that live on other Linux boxes by
SSHing in and running read-only checks — a check is a shell command, so **reading a file is
just `cat`/`grep /path`**. It shells out to the OpenSSH client (already on Win11/Linux) like
`k3s.py` shells to `wsl`; configure targets in `ssh.config.json` (copy the example; the real
file is gitignored). Each target opens **one** SSH session (all its checks run in it) and
targets run in parallel, so an unreachable VM degrades instead of hanging the fleet.
Key-based auth only — set up an SSH key first (`ssh-copy-id`); passwords are disabled
(`BatchMode`), and host-key checking stays on (a new VM must be in `known_hosts`, or set
`"accept_new": true` for trust-on-first-use). Optional `"jump"` routes through a bastion
(`ProxyJump`). A check can carry `warn`/`crit`/`unit` thresholds: numeric results are
threshold-checked into findings, an unreachable target is a WARN, and every scraped value
lands in the snapshot so the chat brain can reason about it ("is the db VM's disk filling
up?"). Runs in the 60s full tier — comfortable for a modest fleet; large fleets want a
trimmed `full` list or a longer collector timeout. Example check with a threshold:
`"disk_root_pct": { "cmd": "df --output=pcent / | tail -1 | tr -dc 0-9", "warn": 85, "crit": 95, "unit": "%" }`.

**Virtual machines & services.** `vm.py` reports Hyper-V VMs and their **encryption posture**
(EncryptStateAndVmMigrationTraffic, virtual TPM, Secure Boot, Shielded) plus running/encrypted
counts — `present:false` when Hyper-V isn't installed (a WSL2-backend box, for instance).
`services.py` reports **systemd** units — running count and any failed units by name — running
natively on a Linux host and, on Windows, bridging into WSL exactly like `k3s.py` (so a Windows
box still watches the services inside its WSL distro). A failed unit surfaces as a finding
(WARN, or CRIT at 3+). Both degrade cleanly where the subsystem is absent.

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
