#!/usr/bin/env python3
# docs/gen_recreate.py — generate docs/RECREATE-WINDOWS.md and docs/RECREATE-LINUX.md from the
# LIVE source. The recreate guides embed every file's full contents; generating them from the
# real files means they can never drift from the code. Re-run after changing any component:
#
#     python docs/gen_recreate.py
#
# Windows guide embeds the actual repo files. Linux guide embeds the shared (cross-platform)
# core from the real files and substitutes Linux translations for the platform-specific
# collectors + the brain's system prompt + device discovery + scheduling.
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read().rstrip("\n")


def block(rel, heading=None, intro=""):
    """A '### heading' + fenced code block embedding the real file at `rel`."""
    lang = "python" if rel.endswith(".py") else ("json" if rel.endswith(".json") else "text")
    head = heading or f"### `{rel}`"
    body = read(rel)
    intro = (intro.strip() + "\n\n") if intro else ""
    return f"{head}\n\n{intro}```{lang}\n{body}\n```\n"


def literal(heading, code, intro="", lang="python"):
    intro = (intro.strip() + "\n\n") if intro else ""
    return f"{heading}\n\n{intro}```{lang}\n{code.rstrip()}\n```\n"


# ------------------------------------------------------------------ shared prose

INTRO = """# Watch Tower — Recreate From Scratch ({plat})

A complete, copy-paste guide to rebuild this project on a fresh {plat} machine. Every file's
full contents are included (generated from the live source by `docs/gen_recreate.py`, so they
match the code exactly), every command shows its expected output. Work top to bottom.

> Sibling guide: `{sibling}`. This file is {plat}-only. For a component/config *reference*
> (what each file does, every knob, remote monitoring, NiFi, SSH), see `docs/INSTRUCTIONS.md`.

---

## 0. What you are building

**Watch Tower** is a local, read-only PC health tool with three layers:

1. **Truth layer (`sysdiag` + `collectors/`)** — standalone scripts that read real sensors and
   each print one JSON object; `sysdiag.py` runs them all in parallel and merges the result;
   `rules.py` turns that snapshot into severity-ranked findings.
2. **A from-scratch character-level GPT (`gpt.py` + `train.py`)** — trained on *synthetic*
   snapshots so it learns to write a short health report from a metrics line. No downloads.
3. **A big-model chat brain (`brain.py` + `context.py`)** — talks to **Ollama** running
   `qwen2.5:32b` locally, grounded in the live snapshot + findings + trends. Exposed as a CLI
   (`chat.py`) and a Gradio web app (`app.py`) with a host selector, live graphs, and history.

```
collectors/*.py ──► sysdiag.py ──► snapshot{{json}} ──► rules.py ──► findings[]
                                        │
        ┌────────────────────────────────┼─────────────────────────────────┐
        ▼                               ▼                                   ▼
  schema.serialize ─► tiny GPT   context.build ─► brain.ask ─► Ollama   live.py ring ─► graphs
```

Two independent "AIs": the **tiny GPT you train** (offline, ~47 MB checkpoint, ~11 M params) and
the **Ollama chat model** (downloaded, e.g. `qwen2.5:32b` ~19 GB — see §7 for the model matrix).
They are separate — run the dashboard with either, both, or neither.

Beyond the health panel the dashboard has: a **Host** selector (local, or many remote machines),
**live graphs** and a **History graph**, a **Search** box (find any logged metric by component,
computer, or date/time), and **shared Notes** (any user of the instance leaves notes the others
see). A `sysdiag.py` run also returns a severity **exit code** (0 clean / 1 WARN / 2 CRIT) so
Task Scheduler or CI can detect machine distress without parsing text.

> **Network honesty:** Watch Tower is local-first (dashboard binds `127.0.0.1`, Ollama is local,
> no API keys), but it is **not** zero-egress: `collectors/net.py` pings `1.1.1.1` and resolves a
> DNS name over the internet each full-fleet cycle to measure connectivity, and remote mode streams
> snapshots to the monitoring host. Everything else stays on the box. Delete/relax `net.py` if you
> want a truly offline build.

Beyond the basics this build includes: deep sensors (VRM/NVMe temps, AIO liquid temp, GPU
throttle/PCIe), boot/power forensics, RGB state, Hyper-V/libvirt VM encryption posture, systemd
services, an **in-app live sampler** with graphs, **remote monitoring** (one dashboard watches
many machines via `ship.py`/NiFi), an **SSH collector** that scrapes remote Linux VMs, and
device discovery. See `docs/INSTRUCTIONS.md` for the reference on those.

---
"""

ML_CORE_INTRO = """## 3. The machine-learning core (offline tiny GPT)

These files build, train, and run a character-level transformer with zero downloads. They are
**identical across Windows and Linux** (pure Python + torch).

**How to train the narrator** (details in §6.3): `data.py` synthesizes a deterministic corpus of
`INPUT metrics → REPORT` documents from random-but-seeded snapshots (seed 1337, so `corpus.txt` is
byte-reproducible); `gpt.py` is the ~11 M-param model (6 layers, 384-dim, `block_size=512` — large
enough that the longest report fits the attention window so multi-finding reports aren't truncated
mid-sentence); `train.py` runs ~3 min on a modern GPU (or ~20–30 min CPU) to val-loss ≈ 0.19 and
writes `ckpt.pt` (~47 MB) + `vocab.json`; `infer.py --demo` shows INPUT / rule-truth / model-output
side by side. **Retrain when** you change `schema.serialize_metrics`, `data.render_report`, or the
corpus size — the model input/label contract changed. You do **not** need to retrain to add
collectors or rules that the narrator's 10-metric input doesn't include (those surface via the
rules engine and chat brain instead).
"""

BUILD_STEPS = """## 6. Build it — step by step (with expected output)

### 6.1 Virtual env + dependencies
{venv}
Confirm torch sees your GPU:
```{sh}
python -c "import torch,gradio,pandas; print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
```
> `cuda True` means the GPU is visible. `False` still runs (the GPT trains on CPU in minutes; the
> 32B Ollama model wants a GPU to be usable).

### 6.2 Sanity-check the pure-logic modules
```{sh}
python schema.py
python rules.py
python live.py
python collectors/docker.py --test
```
Expected: `schema ok`, `rules ok`, `live ok — ...`, `docker parsers ok`.

### 6.3 Generate the corpus, train, test the GPT
```{sh}
python data.py 8000        # -> wrote corpus.txt: 8000 docs (deterministic, seed 1337)
python train.py            # -> ~3 min on a CUDA GPU (bf16) / ~20-30 min CPU; val loss ~0.19;
#                             writes ckpt.pt (~47 MB) + vocab.json
python infer.py --demo     # -> MODEL OUTPUT should read like the GROUND TRUTH
```
> `corpus.txt`, `vocab.json`, and `ckpt.pt` are **generated artifacts** — regenerable and
> git-ignored. `data.py` is deterministic, so the corpus reproduces byte-for-byte. Retrain
> whenever you change `schema.serialize_metrics` / `data.render_report` / the corpus size.

### 6.4 Run the live collectors
{collectors_run}

### 6.5 Full live snapshot as JSON
```{sh}
python sysdiag.py diag --json
```
A big pretty-printed JSON object with every collector's namespace — exactly what `context.py`
feeds the chat model, and what `ship.py` streams in remote mode.

### 6.6 Discover devices (optional)
```{sh}
python sysdiag.py discover           # list known devices -> collector coverage
python sysdiag.py discover --spawn   # stub a collector for a recognized, uncovered device
```

---
"""

OLLAMA = """## 7. Connect Ollama (the chat brain)

1. Install Ollama — it serves on `127.0.0.1:11434`.
2. Pull the default model (~19 GB): `ollama pull qwen2.5:32b`
3. Verify: `ollama run qwen2.5:32b "say OK"` → `OK`.
4. Check it's resident: `ollama ps`.

Smoke-test the brain (Ollama up): `python brain.py` → `brain ok: <a sentence about your machine>`.

`brain.py` knobs: `MODEL` (any tag from `ollama list`), `num_ctx` (context window), `keep_alive`
(`"30m"` — how long it stays in VRAM; `app.py`/`chat.py` run `ollama stop` on clean exit),
`temperature` (`0.3` — low, this is diagnostics not creative writing).

### 7.1 Which model for which GPU — the brain matrix

Rule of thumb: **VRAM needed ≈ model weights + KV-cache(`num_ctx`)**. The KV cache for `num_ctx`
tokens is roughly `num_ctx × n_layer × 2 × hidden × 2 bytes`; the practical numbers below already
include it. Pick the largest model whose "≈VRAM @ ctx" fits with headroom for your desktop/games.
All are one `ollama pull <tag>` and one edit to `MODEL` in `brain.py` — identical code path.

| Model (`ollama pull`) | Origin | Weights | Good `num_ctx` | ≈VRAM (weights+KV) | Fits GPU | Notes |
|---|---|---|---|---|---|---|
| `qwen2.5:32b` **(default)** | Alibaba | ~19 GB | 32768 | ~28 GB | 32 GB (5090/4090-48) | best grounding here; the shipped default |
| `gemma3:27b` | Google | ~17 GB | 16384 | ~23 GB | 24–32 GB | strong US-built alternative |
| `gpt-oss:20b` | OpenAI | ~14 GB | 16384 | ~18 GB | 20–24 GB | US-built, roomy on 24 GB |
| `qwen2.5:14b` | Alibaba | ~9 GB | 16384 | ~12 GB | 12–16 GB | great quality/size trade |
| `phi4` (14b) | Microsoft | ~9 GB | 16384 | ~12 GB | 12–16 GB | US-built, sharp reasoning |
| `qwen2.5:7b` / `llama3.1:8b` | Alibaba / Meta | ~5 GB | 16384 | ~7 GB | 8 GB (3070/4060) | the 8 GB sweet spot |
| `granite3.3:8b` | IBM | ~5 GB | 8192 | ~7 GB | 8 GB | US-built (IBM), enterprise-tuned |
| `llama3.2:3b` / `gemma3:4b` | Meta / Google | ~2–3 GB | 8192 | ~4 GB | 4–6 GB or CPU | usable on a small GPU |
| `phi4-mini` / `qwen2.5:3b` | Microsoft / Alibaba | ~2 GB | 8192 | ~3 GB | CPU-ok | last resort, still grounded |

If a model won't fit, **lower `num_ctx` first** (halving it roughly halves the KV cache) before
dropping to a smaller model — grounding quality tracks model size more than context length here.
On a shared desktop, leave 4–6 GB of VRAM free for the display/compositor and any game.

> **Note — this is not a leaderboard.** All of these produce a grounded answer because the
> *findings* and *live snapshot* are handed to the model as ground truth; a bigger model mainly
> writes cleaner fix-it steps and follows the "advise-only / cite-the-numbers" rules more reliably.

### 7.2 Embedding model (for the optional RAG in §12)

Separate, tiny, and only loaded when you use RAG: `ollama pull mxbai-embed-large` (~670 MB,
1024-dim — measured best on this repo's docs). `nomic-embed-text` (~270 MB, 768-dim) is a lighter
alternative; switch `EMBED_MODEL` + the task prefixes in `rag.py` together (see §12).

---

## 8. Run it

### CLI chat
```{sh}
python chat.py
```
Banner, then a prompt. Ask "Is my GPU temp normal?" — grounded answer. `exit` frees VRAM.

### Web dashboard
```{sh}
{launch}
```
Opens `http://127.0.0.1:7860`: host selector, live stats/findings panel (5 s), chat, live graphs,
History graph, plus a **Search** accordion (query every logged snapshot by component / computer /
date-time) and a **Shared notes** accordion (any user leaves a note the others see; persisted in
`notes.db`). **Ctrl+C** to stop (frees VRAM). **Restart `app.py` after editing any `.py`** — Gradio
caches modules. The port is env-overridable (`WATCHTOWER_PORT`) so a second instance can run
alongside a local one.

> The **History graph** and **Search** read `history.db`, which is filled by the scheduled
> `history.py` logger (§10). A fresh install shows an empty graph until the logger has run a few
> times — run `python history.py` a handful of times to seed it, or wait for the schedule.

---
"""

REMOTE = """## 9. Remote monitoring, multi-host & NiFi

Collectors run on the **monitored** machine; the dashboard/rules/chat run on the **monitoring**
machine; the tiny NanoGPT narrator is portable. The agent side is stdlib-only — copy
`collectors/`, `sysdiag.py`, `ship.py` (no pip installs).

```{sh}
# on the MONITORED machine (agent) — add --narrate to ship NanoGPT reports too
set WATCHTOWER_SHIP_URL=http://<nifi-or-gui-host>:8081/watchtower
set WATCHTOWER_TOKEN=<shared-secret>
python ship.py

# on the MONITORING machine (dashboard)
set WATCHTOWER_REMOTE=1
set WATCHTOWER_TOKEN=<shared-secret>
python app.py
```

Per-machine identity/format lives in `ship.config.json` (copy `ship.config.example.json`):
`host` names the reporter, `label`/`tags` show on the panel, `fast`/`full` pick the collector
tiers. Each distinct `host` gets its own ring; the dashboard's **Host** selector switches the
panel/graphs/chat between machines. `WATCHTOWER_REMOTE=1` runs a token-gated HTTP receiver
(`POST /ingest`, default `0.0.0.0:7861`) instead of the local sampler.

**Apache NiFi** (optional middle hop) buys durable queueing, provenance, and fan-out — minimal
flow is two processors: **ListenHTTP** (Port `8081`, Base Path `watchtower`, forward header
`X-Watchtower-Token`) → **InvokeHTTP** (POST `http://<gui-host>:7861/ingest`, send header
`X-Watchtower-Token`). Full detail + config in `docs/INSTRUCTIONS.md` §7.

### SSH: scrape remote Linux VMs
`collectors/ssh.py` SSHes into Linux VMs and runs read-only checks (a check is a shell command;
reading a file = `cat`/`grep`). Configure `ssh.config.json` (copy `ssh.config.example.json`):
key-based auth only, host-key checking on, per-check `warn`/`crit` thresholds (direction inferred
from `crit`≷`warn`), unreachable = WARN, ~20 s wall-clock budget. See `docs/INSTRUCTIONS.md` §8.

---
"""

# ------------------------------------------------------------------ collector lists

WIN_COLLECTORS = [
    ("cpu", "Core counts + live load + true current clock (turbo-aware) + fastest single-core clock."),
    ("mem", "RAM used %, per-DIMM inventory, commit-charge % (the real allocation-pressure metric), DRAM speed."),
    ("disk", "Used % AND absolute free GB per fixed drive (free GB lets rules downgrade a big-drive pct-CRIT)."),
    ("gpu", "nvidia-smi: util/temp/power/VRAM + fan %, P-state, clocks, PCIe link gen/width, throttle reasons, driver."),
    ("sensors", "Reads LibreHardwareMonitor's whole tree (all temps incl. AIO liquid, fans + pump, rail voltages,"
                " power draws); `liquidctl` fallback for the AIO when LHM is down."),
    ("net", "Ping 1.1.1.1 + gateway (LAN-vs-WAN fault isolation), NIC error counters, cold/warm DNS timing, resolver in use."),
    ("docker", "Container states PARSED to numbers — running/restarting/unhealthy/exited/paused + explicit daemon reachability."),
    ("k3s", "k3s pods via WSL; judges containerStatuses (catches CrashLoopBackOff that phase='Running' hides) + not-ready."),
    ("whea", "Windows hardware-error channel — 7-day-WINDOWED uncorrected count + corrected-machine-check count, Level-based."),
    ("tpm", "TPM presence/version via `tpmtool` (works UNELEVATED, unlike Get-Tpm)."),
    ("me", "Intel Management Engine presence/version."),
    ("usb", "USB device + problem-device counts."), ("storage", "Physical-drive inventory + SMART health/temp."),
    ("os", "OS posture: uptime, pending-reboot, CPU microcode (14900K Vmin-shift fix = 0x12B+), BIOS, update age, Secure Boot."),
    ("security", "Defender real-time protection + signature age, firewall, VBS/HVCI, BitLocker, failed-logon count."),
    ("events", "Event-log health: WDDM TDR GPU resets (4101), app crashes (1000), NTFS corruption (55), failed scheduled tasks."),
    ("procs", "Top CPU / RAM / per-process GPU-VRAM consumers (names the chat model's own footprint)."),
    ("wsl", "The WSL2 utility VM Docker/k3s run inside — vmmem working set + ext4 vhdx size (both otherwise invisible)."),
    ("power", "Boot/power forensics from the event log (Kernel-Power 41 / 6008 / throttle 37)."),
    ("lights", "Board/RGB zone state via the OpenRGB SDK server (127.0.0.1:6742)."),
    ("vm", "Hyper-V VMs + their encryption posture (encrypted state, vTPM, Secure Boot, Shielded)."),
    ("services", "systemd units via `wsl systemctl` (bridges into WSL like k3s.py); running + failed."),
    ("ssh", "Scrape remote Linux VMs over SSH — read-only checks with thresholds. See INSTRUCTIONS §8."),
]
SDR_COLLECTORS = [
    ("_sdr_common", "Shared SDR probe (underscore = library, snapshot() skips it)."),
    ("sdr", ""), ("rx", ""), ("tx", ""), ("tuner", ""), ("antenna", ""),
]

# Modules common to both platforms (embedded from the real files).
CORE_ML = ["schema.py", "rules.py", "data.py", "gpt.py", "train.py", "infer.py"]
CORE_APP = ["sysdiag.py", "history.py", "live.py", "trends.py", "search.py", "notes.py",
            "context.py", "rag.py", "art.py", "app.py", "chat.py", "ship.py", "discover.py"]


def collectors_section_windows():
    parts = ["## 4. The collectors (live sensors)\n",
             "Each is a standalone script that prints one namespaced JSON object and **degrades**"
             " (never crashes) when its hardware/subsystem is absent. Create `collectors/` and add"
             " each file.\n"]
    for name, intro in WIN_COLLECTORS:
        parts.append(block(f"collectors/{name}.py", f"### `collectors/{name}.py`", intro))
    parts.append("### SDR / antenna skeletons\n\n"
                 "These run today (emit `present:false`) and carry `FILL-ME` blocks to complete when"
                 " the radio arrives. `_sdr_common.py` is shared (underscore = library).\n")
    for name, intro in SDR_COLLECTORS:
        parts.append(block(f"collectors/{name}.py", f"### `collectors/{name}.py`", intro))
    return "\n".join(parts)


# ------------------------------------------------------------------ Windows doc

def gen_windows():
    doc = [INTRO.format(plat="Windows", sibling="RECREATE-LINUX.md")]
    doc.append("""## 1. Prerequisites (install these first)

| Tool | Why | Install |
|---|---|---|
| **Python 3.10+** (tested 3.14.3) | runs everything | python.org → check "Add to PATH" |
| **NVIDIA driver + CUDA GPU** | trains the GPT; runs the 32B model | `nvidia-smi` must work |
| **Ollama** | serves the 32B chat model | ollama.com/download |
| **LibreHardwareMonitor** | the ONLY source of CPU/liquid temp + fan RPM on Windows | its GitHub |
| **OpenSSH client** (built into Win11) | the `ssh` collector | already present |
| **Docker Desktop** *(optional)* | the `docker`/`k3s` collectors | docker.com |
| **OpenRGB** *(optional)* | the `lights` collector (run its SDK server) | openrgb.org |

**LibreHardwareMonitor:** run it (as Administrator for full sensors), Options → **Run web
server** (port 8085), confirm http://127.0.0.1:8085/data.json shows JSON, leave it running.

---

## 2. Create the project folder

```powershell
mkdir C:\\Users\\<you>\\sysdiag; cd C:\\Users\\<you>\\sysdiag; mkdir collectors, docs
```

---
""")
    doc.append(ML_CORE_INTRO)
    for f in CORE_ML:
        doc.append(block(f))
    doc.append(collectors_section_windows())
    doc.append("## 5. Truth-layer aggregator, live sampler, chat brain & UI\n")
    for f in CORE_APP:
        doc.append(block(f))
    doc.append(block("brain.py"))
    doc.append(block("system_facts.md", "### `system_facts.md` (edit for YOUR machine)",
                     "Static facts the chat reads every message. Replace with your CPU/GPU model,"
                     " normal temps, and what you care about."))
    doc.append(block("ship.config.example.json", "### `ship.config.example.json`",
                     "Copy to `ship.config.json` on each monitored machine (gitignored)."))
    doc.append(block("ssh.config.example.json", "### `ssh.config.example.json`",
                     "Copy to `ssh.config.json` where the ssh collector runs (gitignored)."))
    doc.append(block(".gitignore"))
    doc.append(BUILD_STEPS.format(
        sh="powershell",
        venv="```powershell\npython -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\n"
             "python -m pip install --upgrade pip\n"
             "pip install torch --index-url https://download.pytorch.org/whl/cu128\n"
             "pip install gradio pandas sqlite-vec\n"
             "# sqlite-vec powers the optional RAG (§12); everything else the app uses is stdlib.\n"
             "# optional deep-sensor deps: pip install liquidctl openrgb-python\n```",
        collectors_run="With LibreHardwareMonitor running:\n```powershell\npython collectors\\gpu.py\n"
                       "python collectors\\sensors.py\npython sysdiag.py\n```\n> `tpm` blank and"
                       " unelevated `storage` wear/temp null are expected — run PowerShell **as"
                       " Administrator** for full detail."))
    doc.append(OLLAMA.format(sh="powershell",
                             launch="$env:PYTHONIOENCODING = \"utf-8\"; python app.py"))
    doc.append(REMOTE.format(sh="powershell"))
    doc.append("""## 10. Schedule history logging (the History graph's data)

`history.py` appends one snapshot to `history.db` per run. Schedule it every ~15 min:

```powershell
$py  = "C:\\Users\\<you>\\sysdiag\\.venv\\Scripts\\python.exe"
$arg = "C:\\Users\\<you>\\sysdiag\\history.py"
$act = New-ScheduledTaskAction -Execute $py -Argument $arg -WorkingDirectory "C:\\Users\\<you>\\sysdiag"
$trg = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "WatchTowerHistory" -Action $act -Trigger $trg
```

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Chat: `HTTP 400: cannot unmarshal array` | Gradio sent list-shaped content | `_text()` in `brain.py` already coerces it |
| Chat replies one word then stops | system prompt filled `num_ctx` | lower RAG `TOP_K` / raise `MIN_SCORE`; keep `num_ctx` ≥ prompt + reply |
| `(couldn't reach Ollama …)` | service down / model not pulled | `ollama ps`, `ollama pull qwen2.5:32b` |
| `sensors: LHM not reachable` | LHM not running / web server off | start LHM, enable Run web server (8085) |
| Live graph blank | opened before the ring filled | wait ~10 s; the plot rebuilds each tick |
| `services` shows `error` on Windows | a WSL/systemd UTF-8 decode issue | fixed — the collector decodes utf-8/replace |
| Edited a file, app unchanged | Gradio cached the module | restart `app.py` |
| Banner crashes launch | cp1252 stdout | set `PYTHONIOENCODING=utf-8` (or already-guarded in `art.py`) |

---
""")
    doc.append(RAG_SECTION)
    return "\n".join(doc)


# ------------------------------------------------------------------ Linux doc

# Linux translations for the platform-specific collectors. Cross-platform collectors
# (docker, ssh, sdr family, lights via OpenRGB, services native systemd) reuse the real files.
LINUX_COLLECTORS_INTRO = """## 4. The collectors (live Linux sensors)

Each is a standalone script that prints one namespaced JSON object and **degrades** when its
subsystem is absent. Several are cross-platform and identical to the Windows repo files
(`docker`, `ssh`, the `sdr`/`rx`/`tx`/`tuner`/`antenna` skeletons, `lights` via OpenRGB, and
`services` — which already runs native `systemctl` on Linux). The hardware collectors below are
Linux-native (psutil / lm-sensors / journalctl / lspci) — the shared `schema.py`/`rules.py` are
unchanged, and root `/` is aliased to the disk key `C` so the trained model's `disk_C` input
stays populated.

> Install the Linux sensor deps: `pip install psutil` and `sudo apt install lm-sensors
> smartmontools usbutils` then `sudo sensors-detect`. GPU/Docker/k3s/SSH collectors need their
> respective tools (`nvidia-smi`, `docker`, `k3s`, `ssh`).
>
> **Omitted on Linux:** `tpm.py`, `me.py`, `os.py`, `security.py`, `events.py`, and `wsl.py` are
> Windows-specific (Get-Tpm / Intel ME / registry+event-log / Defender+BitLocker / the WSL VM).
> Skip them; the shared `rules.py` simply sees no such keys. Linux analogues if you want them:
> TPM via `/sys/class/tpm/`, uptime via `/proc/uptime`, security via `ufw`/`aa-status`, events via
> `journalctl`. `procs.py` below is the Linux port (psutil); the rest of the fleet is native.

> **Hardware-verification status.** These collectors were logic-tested in WSL (a real Linux
> userland with **no** lm-sensors chips and **no** SMART-capable drives), so the hardware-shaped
> parsing has not run against live silicon. The two parsers with real structure — `sensors.py`
> (psutil/hwmon label matching for cpu_temp / liquid_temp / pump_rpm) and `storage.py`
> (`smartctl --scan` + `smartctl -H -A -j` JSON) — are **fixture-tested** in the repo
> (`tests/test_linux_parsers.py`) against realistic lm-sensors and smartmontools-JSON samples,
> but remain **unverified on live hardware**: your chip's labels may differ (check `sensors`
> output and adjust the match lists). The line-oriented scrapers (`whea.py`/`power.py` grep
> journalctl text, `vm.py` parses `virsh list`) are trivially shaped but equally unverified on a
> real MCE/libvirt box — treat first-run output on real hardware as something to eyeball once.
"""

LINUX_CPU = '''# collectors/cpu.py (Linux) — core counts + live load via psutil.
import json
try:
    import psutil
    print(json.dumps({"cpu": {"cores": psutil.cpu_count(logical=False),
                              "logical": psutil.cpu_count(logical=True),
                              "load": int(psutil.cpu_percent(interval=0.5))}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))'''

LINUX_MEM = '''# collectors/mem.py (Linux) — RAM used% via psutil.
import json
try:
    import psutil
    print(json.dumps({"mem": {"pct": int(psutil.virtual_memory().percent)}}))
except Exception as e:
    print(json.dumps({"mem": {"error": str(e)}}))'''

LINUX_DISK = '''# collectors/disk.py (Linux) — used% per real mountpoint; root '/' aliased to "C"
# so the trained model's shared `disk_C` input stays populated.
import json, shutil, psutil
out = {}
for p in psutil.disk_partitions(all=False):
    if "loop" in p.device or not p.mountpoint:
        continue
    try:
        pct = int(shutil.disk_usage(p.mountpoint).used * 100 / shutil.disk_usage(p.mountpoint).total)
    except OSError:
        continue
    key = "C" if p.mountpoint == "/" else p.mountpoint.strip("/").replace("/", "_") or "root"
    out[key] = pct
print(json.dumps({"disk": out}))'''

LINUX_SENSORS = '''# collectors/sensors.py (Linux) — CPU package temp + fan RPM via lm-sensors (psutil).
# Needs `lm-sensors` installed and `sudo sensors-detect` run once. Reports the same keys the
# shared rules.py/schema.py expect (cpu_temp, fans) plus a full temps map + liquid_temp if the
# AIO exposes one to lm-sensors.
import json
try:
    import psutil
    temps, fans = {}, {}
    for chip, entries in (psutil.sensors_temperatures() or {}).items():
        for e in entries:
            temps[f"{chip}: {e.label or 'temp'}"] = e.current
    for chip, entries in (psutil.sensors_fans() or {}).items():
        for e in entries:
            fans[f"{chip}: {e.label or 'fan'}"] = e.current
    cpu = [v for k, v in temps.items() if any(t in k.lower() for t in ("package", "tctl", "coretemp", "k10temp"))]
    liquid = next((v for k, v in temps.items() if any(t in k.lower() for t in ("liquid", "coolant", "water"))), None)
    print(json.dumps({"sensors": {"cpu_temp": int(max(cpu)) if cpu else None,
                                  "fans": fans, "temps": temps, "liquid_temp": liquid,
                                  "pump_rpm": next((v for k, v in fans.items() if "pump" in k.lower()), None)}}))
except Exception as e:
    print(json.dumps({"sensors": {"error": str(e)}}))'''

LINUX_NET = '''# collectors/net.py (Linux) — ping 1.1.1.1 (stdlib) + link/error counters via psutil
# + cold/warm DNS resolve timing (a slow steady-state resolve = a sick resolver).
import json, subprocess, re, socket, time


def ping(host="1.1.1.1"):
    try:
        out = subprocess.run(["ping", "-c", "1", host], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]\\s*([\\d.]+)\\s*ms", out)
        return int(float(m.group(1))) if m else None
    except Exception:
        return None


def dns_ms(name="example.com"):
    t0 = time.perf_counter()
    try:
        socket.getaddrinfo(name, 443)
        return int((time.perf_counter() - t0) * 1000)
    except OSError:
        return None


try:
    import psutil
    up = next((n for n, s in psutil.net_if_stats().items() if s.isup and n != "lo"), None)
    io = psutil.net_io_counters(pernic=True).get(up) if up else None
    print(json.dumps({"net": {"ping_ms": ping(), "target": "1.1.1.1", "dns_ms": dns_ms(),
                              "up": bool(up), "name": up,
                              "rx_errors": getattr(io, "errin", None), "tx_errors": getattr(io, "errout", None)}}))
except Exception as e:
    print(json.dumps({"net": {"error": str(e)}}))'''

LINUX_WHEA = '''# collectors/whea.py (Linux) — Linux has no WHEA; the equivalent is MCE / "Hardware Error"
# events in the kernel log. Count recent ones from journalctl. Key stays "whea" so the shared
# schema.py/rules.py are unchanged. (journalctl -k may need the systemd-journal group / root.)
import json, subprocess
try:
    try:
        out = subprocess.run(["journalctl", "-k", "--since", "-24h", "--no-pager"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20).stdout
    except FileNotFoundError:                     # non-systemd box: no journalctl != broken
        print(json.dumps({"whea": {"present": False, "note": "journalctl not available"}})); raise SystemExit
    errs = [ln for ln in out.splitlines() if "Hardware Error" in ln or "mce:" in ln.lower() or "MCE" in ln]
    print(json.dumps({"whea": {"recent_errors": len(errs), "latest": (errs[-1][:200] if errs else None)}}))
except Exception as e:
    print(json.dumps({"whea": {"error": str(e)}}))'''

LINUX_K3S = '''# collectors/k3s.py (Linux) — k3s runs natively. Uses `sudo -n` so it works unattended IF
# passwordless `k3s kubectl` is allowed; otherwise it degrades. If your user already has
# KUBECONFIG set, change K3S_CMD to ["kubectl","get","pods","-A","-o","json"].
import json, subprocess
K3S_CMD = ["sudo", "-n", "k3s", "kubectl", "get", "pods", "-A", "-o", "json"]
try:
    try:
        r = subprocess.run(K3S_CMD, capture_output=True, text=True, timeout=25)
    except FileNotFoundError:
        print(json.dumps({"k3s": {"present": False, "note": "k3s/sudo not found"}})); raise SystemExit
    if r.returncode != 0:
        err = (r.stderr or "kubectl failed").strip()
        # a sudo/permission problem is a CONFIG issue, not a broken cluster — degrade to a note
        # (present:false) instead of an error, so an unattended box without passwordless sudo
        # doesn't fire a WARN every run. Adjust K3S_CMD (kubeconfig / drop sudo) to enable.
        if any(w in err.lower() for w in ("sudo", "password", "authentication", "permission")):
            print(json.dumps({"k3s": {"present": False, "note": "kubectl not reachable (sudo/kubeconfig): " + err[:120]}}))
        else:
            print(json.dumps({"k3s": {"error": err[:200]}}))
    else:
        items = json.loads(r.stdout).get("items", [])
        pods = [{"name": i["metadata"]["name"], "namespace": i["metadata"]["namespace"],
                 "phase": i.get("status", {}).get("phase")} for i in items]
        running = sum(1 for p in pods if p["phase"] == "Running")
        print(json.dumps({"k3s": {"running": running, "total": len(pods), "pods": pods}}))
except Exception as e:
    print(json.dumps({"k3s": {"error": str(e)}}))'''

LINUX_USB = '''# collectors/usb.py (Linux) — USB device count via lsusb (apt install usbutils).
import json, subprocess
try:
    out = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=10).stdout
    n = len([ln for ln in out.splitlines() if ln.strip()])
    print(json.dumps({"usb": {"devices": n, "problems": 0}}))
except FileNotFoundError:
    print(json.dumps({"usb": {"present": False, "note": "lsusb not installed (apt install usbutils)"}}))
except Exception as e:
    print(json.dumps({"usb": {"error": str(e)}}))'''

LINUX_STORAGE = '''# collectors/storage.py (Linux) — drive health via smartctl (apt install smartmontools).
# SMART usually needs root, so unprivileged this degrades. Uses `smartctl --scan` then queries.
import json, subprocess
def sc(*a):
    return subprocess.run(["smartctl", *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=20)
try:
    scan = sc("--scan").stdout
    drives = []
    for ln in scan.splitlines():
        dev = ln.split()[0] if ln.strip() else None
        if not dev:
            continue
        r = sc("-H", "-A", "-j", dev)
        try:
            d = json.loads(r.stdout)
            # NVMe drives report NO rotation_rate key at all — protocol is the SSD signal there;
            # SATA SSDs report rotation_rate 0. A failed SMART self-test must read "Failed"
            # (rules.py's bad-health allow-list fires CRIT on it); "Unknown" only when absent.
            ssd = d.get("device", {}).get("protocol") == "NVMe" or d.get("rotation_rate", 1) == 0
            passed = d.get("smart_status", {}).get("passed")
            drives.append({"name": d.get("model_name", dev), "media": "SSD" if ssd else "HDD",
                           "health": {True: "Healthy", False: "Failed"}.get(passed, "Unknown"),
                           "temp": d.get("temperature", {}).get("current")})
        except Exception:
            drives.append({"name": dev, "health": "Unknown"})
    print(json.dumps({"storage": {"drives": drives, "disk_events_24h": 0}}))
except FileNotFoundError:
    print(json.dumps({"storage": {"present": False, "note": "smartctl not installed / needs root"}}))
except Exception as e:
    print(json.dumps({"storage": {"error": str(e)}}))'''

LINUX_POWER = '''# collectors/power.py (Linux) — power/boot forensics: unclean shutdowns via the journal's
# boot list vs `last -x` reboots, and thermal-throttle messages in the kernel log. The Linux
# analogue of the Windows Kernel-Power 41 / throttle-37 collector. Keys mirror the Windows one.
import json, subprocess
def jr(*a):
    # a MISSING optional tool (last/journalctl not installed) is not a broken data source —
    # return "" so that signal just reads 0, never erroring the whole collector.
    try:
        return subprocess.run(a, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=20).stdout
    except FileNotFoundError:
        return ""
try:
    boots = jr("journalctl", "--list-boots", "--no-pager")
    # an unclean shutdown shows a boot with no clean "systemd-shutdown" at its tail; approximate
    # with `last -x | grep crash` (kernel crash/abrupt) counts over the recent window.
    crashes = len([ln for ln in jr("last", "-x", "-n", "50").splitlines() if "crash" in ln.lower()])
    throttle = len([ln for ln in jr("journalctl", "-k", "--since", "-24h", "--no-pager").splitlines()
                    if "thermal" in ln.lower() and ("throttl" in ln.lower() or "critical" in ln.lower())])
    print(json.dumps({"power": {"dirty_reboots_7d": crashes, "unexpected_shutdowns_7d": crashes,
                                "cpu_throttle_events_24h": throttle}}))
except Exception as e:
    print(json.dumps({"power": {"error": str(e)}}))'''

LINUX_VM = '''# collectors/vm.py (Linux) — KVM/libvirt VMs + LUKS/confidential-computing encryption
# posture (the Linux analogue of the Windows Hyper-V collector). Needs libvirt (`virsh`).
# "encrypted" here = the domain XML declares a launch-security type (SEV/SEV-SNP/TDX) or a
# LUKS-backed disk; adapt to your definition. Degrades to present:false without libvirt.
import json, shutil, subprocess
if not shutil.which("virsh"):
    print(json.dumps({"vm": {"present": False}}))
    raise SystemExit
def vsh(*a):
    return subprocess.run(["virsh", *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=20).stdout
try:
    names = [ln.split(None, 2)[1] for ln in vsh("list", "--all").splitlines()[2:] if ln.split()[1:2]]
    vms = []
    for n in names:
        state = "Running" if "running" in vsh("domstate", n).lower() else "Off"
        xml = vsh("dumpxml", n)
        enc = ("launchSecurity" in xml) or ("luks" in xml.lower())
        vms.append({"name": n, "state": state, "encrypted": enc,
                    "vtpm": "<tpm" in xml.lower(), "secure_boot": "loader secure='yes'" in xml.lower()})
    if not vms:
        print(json.dumps({"vm": {"present": False}}))
    else:
        print(json.dumps({"vm": {"present": True, "total": len(vms),
                                 "running": sum(1 for v in vms if v["state"] == "Running"),
                                 "encrypted": sum(1 for v in vms if v["encrypted"]), "vms": vms}}))
except Exception as e:
    print(json.dumps({"vm": {"error": str(e)}}))'''

LINUX_DISCOVER_NOTE = """### `discover.py` (Linux)

The Windows `discover.py` scans PnP + COM ports. On Linux, replace the `scan_pnp()` body to parse
`lsusb`/`lspci` (VID:PID) and `/dev/ttyUSB*` / `/dev/ttyACM*` for serial ports; keep the same
`DEVICE_MAP` / `_sdr_common.KNOWN` mapping and `--spawn` stub logic. The collectors it maps to are
cross-platform, so only the scan front-end changes.
"""

LINUX_PROCS = '''# collectors/procs.py (Linux) — top CPU / RAM consumers via psutil, plus per-process
# GPU VRAM via nvidia-smi where present. Same keys the Windows procs.py emits.
import json, shutil, subprocess
try:
    import psutil
    for p in psutil.process_iter(["name"]):      # prime cpu_percent (first call returns 0.0)
        try: p.cpu_percent()
        except Exception: pass
    import time; time.sleep(0.3)
    rows = []
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            rows.append((p.info["name"], p.cpu_percent(), p.info["memory_info"].rss))
        except Exception:
            continue
    n = psutil.cpu_count() or 1
    top_cpu = [{"name": nm, "cpu_pct": round(c / n, 1)} for nm, c, _ in
               sorted(rows, key=lambda r: -r[1])[:5]]
    top_mem = [{"name": nm, "mem_mb": int(m / 1048576)} for nm, _, m in
               sorted(rows, key=lambda r: -r[2])[:5]]
    out = {"top_cpu": top_cpu, "top_mem": top_mem}
    smi = shutil.which("nvidia-smi")
    if smi:
        r = subprocess.run([smi, "--query-compute-apps=process_name,used_memory",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=6)
        gv = []
        for ln in r.stdout.strip().splitlines():
            if "," in ln:
                nm, mb = ln.rsplit(",", 1)
                try: gv.append({"name": nm.strip(), "vram_mb": int(float(mb))})
                except ValueError: pass
        out["top_gpu_vram"] = sorted(gv, key=lambda x: -x["vram_mb"])[:5]
    print(json.dumps({"procs": out}))
except Exception as e:
    print(json.dumps({"procs": {"error": str(e)}}))'''

LINUX_COLLECTOR_MAP = [
    ("cpu", LINUX_CPU, ""), ("mem", LINUX_MEM, ""), ("disk", LINUX_DISK, ""),
    ("sensors", LINUX_SENSORS, ""), ("net", LINUX_NET, ""), ("whea", LINUX_WHEA, ""),
    ("k3s", LINUX_K3S, ""), ("usb", LINUX_USB, ""), ("storage", LINUX_STORAGE, ""),
    ("power", LINUX_POWER, ""), ("vm", LINUX_VM, ""), ("procs", LINUX_PROCS, ""),
]
# these collector files are cross-platform — embed the REAL repo file in the Linux guide too
LINUX_SHARED_COLLECTORS = ["gpu", "docker", "services", "ssh",
                           "_sdr_common", "sdr", "rx", "tx", "tuner", "antenna", "lights"]


def collectors_section_linux():
    parts = [LINUX_COLLECTORS_INTRO]
    for name, src, intro in LINUX_COLLECTOR_MAP:
        parts.append(literal(f"### `collectors/{name}.py` (Linux)", src, intro))
    parts.append("### Cross-platform collectors (identical to the Windows repo files)\n\n"
                 "These need no Linux changes — `gpu` (nvidia-smi), `docker`, `services` (native"
                 " `systemctl`), `ssh`, `lights` (OpenRGB SDK), and the SDR skeletons. Embedded"
                 " here for completeness.\n")
    for name in LINUX_SHARED_COLLECTORS:
        parts.append(block(f"collectors/{name}.py", f"### `collectors/{name}.py`"))
    return "\n".join(parts)


def linux_brain():
    """The real brain.py with its system prompt adapted from Windows/PowerShell to Linux/bash."""
    src = read("brain.py")
    src = src.replace("THIS\nspecific Windows 11 PC", "THIS\nspecific Linux machine")
    src = src.replace("the shell — PowerShell", "the shell — bash")
    src = src.replace("Prefer built-in Windows/PowerShell commands", "Prefer built-in Linux/coreutils commands")
    src = src.replace('open Windows Terminal / PowerShell "as Administrator"', "prefix with `sudo`")
    src = src.replace("ELEVATED (Administrator) shell", "root/sudo")
    return literal("### `brain.py` (system prompt adapted for Linux/bash/sudo)", src,
                   "Identical to the Windows `brain.py` except the system prompt speaks bash/sudo"
                   " instead of PowerShell/Administrator.")


def gen_linux():
    doc = [INTRO.format(plat="Linux", sibling="RECREATE-WINDOWS.md")]
    doc.append("""## 1. Prerequisites

Debian/Ubuntu shown; translate to your distro.

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git \\
     lm-sensors smartmontools usbutils openssh-client
sudo sensors-detect            # answer the prompts once
pip install psutil             # the Linux collectors use psutil
```

Plus: an **NVIDIA driver** (`nvidia-smi`) for GPU + the 32B model, **Ollama**
(ollama.com/download), and optionally **Docker**, **k3s**, **OpenRGB** (SDK server) for those
collectors.

---

## 2. Create the project folder

```bash
mkdir -p ~/sysdiag/collectors ~/sysdiag/docs && cd ~/sysdiag
```

---
""")
    doc.append(ML_CORE_INTRO)
    for f in CORE_ML:
        doc.append(block(f))
    doc.append(collectors_section_linux())
    doc.append(LINUX_DISCOVER_NOTE)
    doc.append("## 5. Truth-layer aggregator, live sampler, chat brain & UI\n\n"
               "These modules are cross-platform — embedded from the real repo files. Only"
               " `brain.py`'s system prompt is adapted for Linux (below).\n")
    for f in CORE_APP:
        doc.append(block(f))
    doc.append(linux_brain())
    doc.append(block("system_facts.md", "### `system_facts.md` (edit for YOUR machine)"))
    doc.append(block("ship.config.example.json", "### `ship.config.example.json`"))
    doc.append(block("ssh.config.example.json", "### `ssh.config.example.json`"))
    doc.append(BUILD_STEPS.format(
        sh="bash",
        venv="```bash\npython3 -m venv .venv\nsource .venv/bin/activate\n"
             "pip install --upgrade pip\n"
             "pip install torch --index-url https://download.pytorch.org/whl/cu128\n"
             "pip install gradio pandas psutil sqlite-vec\n```",
        collectors_run="```bash\npython collectors/gpu.py\npython collectors/sensors.py\n"
                       "python sysdiag.py\n```\n> `storage` needs root for SMART; `whea`/`power`"
                       " read the journal (systemd-journal group or sudo)."))
    doc.append(OLLAMA.format(sh="bash", launch="python app.py"))
    doc.append(REMOTE.format(sh="bash"))
    doc.append("""## 10. Schedule history logging (the History graph's data)

Cron every ~15 min (absolute paths, the venv python):

```bash
crontab -e
# add:
*/15 * * * * cd ~/sysdiag && ~/sysdiag/.venv/bin/python history.py >> ~/sysdiag/history.log 2>&1
```

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `sensors: {}` / no temps | lm-sensors not detected | `sudo sensors-detect` then re-run |
| `storage` degraded | SMART needs root | run as root or add a sudoers rule for `smartctl` |
| `whea`/`power` empty | no journal access | add your user to `systemd-journal` or use sudo |
| `(couldn't reach Ollama …)` | service down / model not pulled | `ollama ps`, `ollama pull qwen2.5:32b` |
| Live graph blank | opened before the ring filled | wait ~10 s; the plot rebuilds each tick |
| Edited a file, app unchanged | Gradio cached the module | restart `app.py` |

---
""")
    doc.append(RAG_SECTION)
    return "\n".join(doc)


# ------------------------------------------------------------------ RAG section (shared)

RAG_SECTION = """## 12. Add a local RAG pipeline (semantic doc retrieval)

Optional. Everything above gives the chat a *live* picture (snapshot + findings) plus a static
`system_facts.md`. **RAG** adds a *reference library*: point it at any Markdown docs — homelab
notes, hardware manuals, runbooks, scraped wikis — and the model gets only the few paragraphs
relevant to each question, by semantic similarity. Local-only, read-only, degrades to silence if
Ollama is down. It adds **one file** (`rag.py`) and edits **one** (`context.py`); `brain.py` does
not change. Built to scale: it embeds in **batches** and indexes **incrementally**, so a large
corpus builds in minutes and editing one doc re-embeds only that doc.

1. **Pull an embedding model:** `ollama pull mxbai-embed-large` (`sqlite-vec` is already installed
   from §6.1). `mxbai-embed-large` measured best on this repo's docs; `nomic-embed-text` is a
   lighter alternative (switch `EMBED_MODEL` + the task prefixes together — see the note in `rag.py`).
2. **Add `rag.py`** — the real file is embedded below.
3. **Wire it into `context.py`** — the shipped `context.py` already calls
   `rag.context_block(message)` (see its source above), so no edit is needed if you use these
   files as-is.
4. **Build the index:** `python rag.py --build` (re-run anytime; `--build --force` re-embeds all).
5. **Verify:** `python rag.py "how is my reverse proxy set up?"` returns ranked chunks.

`rag.py`'s full source is in §5 above (it's a core file — `context.py` imports it). It uses a
**hybrid retrieval** step: fetch a vector-similarity pool, then re-rank by `0.6·cosine +
0.4·(question↔chunk word overlap)` — the passage that both embeds near the question and shares its
vocabulary. Measured on this repo: that rerank lifted MRR@5 from 0.79 to 0.95. Tuning knobs live at
its top (`RERANK_POOL`/`RERANK_ALPHA`, `TOP_K`, `MIN_SCORE`, `CHUNK_*`, embed model + prefixes) —
the RAG equivalent of `rules.THRESH`. Lower `TOP_K` / raise `MIN_SCORE` if the context gets too big
and the model starts replying in one line.
"""


# ------------------------------------------------------------------ main

def main():
    win = gen_windows()
    lin = gen_linux()
    with open(os.path.join(ROOT, "docs", "RECREATE-WINDOWS.md"), "w", encoding="utf-8") as f:
        f.write(win + "\n")
    with open(os.path.join(ROOT, "docs", "RECREATE-LINUX.md"), "w", encoding="utf-8") as f:
        f.write(lin + "\n")
    print(f"wrote RECREATE-WINDOWS.md ({win.count(chr(10))+1} lines) + "
          f"RECREATE-LINUX.md ({lin.count(chr(10))+1} lines)")


if __name__ == "__main__":
    main()
