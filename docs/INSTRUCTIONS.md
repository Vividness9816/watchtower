# Watch Tower — Instructions & Component Reference

The complete operator's manual: what every component does, everything you can configure,
how to create and edit collectors, how the remote-monitoring / multi-host / SSH features
work, and how the **Apache NiFi** integration is wired and configured.

This is the *reference*. To rebuild the whole project from an empty folder, use
`docs/RECREATE-WINDOWS.md` / `docs/RECREATE-LINUX.md` (they embed every file's full source).

---

## 1. What Watch Tower is

A local, **read-only** machine-health tool with three independent layers:

1. **Truth layer** — `collectors/*.py` read real sensors and each print one JSON object;
   `sysdiag.py` runs them all in parallel and merges the result; `rules.py` turns that
   snapshot into severity-ranked findings. No model, no network required.
2. **Tiny offline GPT** — `gpt.py` + `train.py` train a ~11 M-param char-level transformer
   (6 layers, 384-dim, `block_size=512`) on *synthetic* snapshots so it learns to narrate a health
   report. ~47 MB checkpoint, no downloads, ~3 min to train on a GPU. (`schema.py`/`data.py`/
   `infer.py` support it; see §9 "Train / retrain the narrator".)
3. **Chat brain** — `brain.py` + `context.py` talk to a local **Ollama** model
   (`qwen2.5:32b` by default), grounded in the live snapshot + findings + trends. Surfaced
   as a CLI (`chat.py`) and a Gradio web dashboard (`app.py`).

```
                       ┌── sysdiag.snapshot() runs every collectors/*.py in parallel ──┐
collectors/*.py ──►    │  cpu gpu mem sensors disk net docker k3s whea tpm me usb       │
(one JSON each)        │  storage lights power vm services ssh  + sdr/rx/tx/tuner/antenna│
                       └───────────────────────────┬──────────────────────────────────┘
                                                    ▼   merged snapshot {json}
                                        rules.diagnose() ──► findings[]
                                                    │
        ┌───────────────────────────────────────────┼───────────────────────────────────┐
        ▼                                            ▼                                     ▼
  schema.serialize ─► tiny GPT (infer.py)   context.build ─► brain.ask ─► Ollama    live.py ring ─► graphs
                                                    (chat.py CLI  +  app.py web dashboard)
```

**Local vs remote.** By default the dashboard samples *this* machine. In **remote mode** the
collectors run on other machines (via `ship.py`), stream JSON to the dashboard (directly or
through **NiFi**), and one dashboard watches many hosts — see §6–§8.

---

## 2. Component reference

Every file, what it does, and its main knobs. "Knob" = something you're expected to edit.

### Truth layer

| File | Role | Key knobs |
|---|---|---|
| `sysdiag.py` | Aggregator + CLI. `snapshot()` globs `collectors/*.py` (skips `_*.py`), runs each as its own `python -P` subprocess in a thread pool (25 s per-collector timeout), merges the namespaced JSON. Subcommands: `diag` (default), `net`, `report`, `discover`. | per-collector `timeout=25`; `-P` flag (keeps `collectors/` off the child path so a collector filename can't shadow a pip package) |
| `collectors/*.py` | One sensor each. Standalone script → prints exactly one JSON object namespaced under its own key. Absent hardware **degrades** (`{"present": false}` or a `note`), never crashes. See §3–§4. | each collector's own constants |
| `rules.py` | `diagnose(snapshot) -> findings[]`. Thresholds + cross-signal rules (cooling, PCIe-under-load, dead resolver, failed services, SSH checks…). | `THRESH` dict (warn/crit per metric) — **the main per-machine tuning knob** |
| `schema.py` | The **frozen** train/serve contract. `serialize_metrics(snap)` is the exact text the GPT trains and runs on — keep it stable. `summarize(snap)` is the one-line human summary. | leave `serialize_metrics` stable once trained |

### Live sampling + history

| File | Role | Key knobs |
|---|---|---|
| `live.py` | In-app background sampler. Two tiers: `FAST` collectors every `FAST_S`s, the full fleet every `FULL_S`s, in a ~1 h in-memory ring **per host**. Feeds the panel, live graphs, and chat. In `WATCHTOWER_REMOTE=1` it instead runs the HTTP receiver (`start_receiver`). | `FAST_S=5`, `FULL_S=60`, `FAST=[cpu,gpu,mem,sensors,disk]`, `METRICS` (graphable label→path), `SPANS` |
| `history.py` | Appends one full snapshot to `history.db` (SQLite, one row = `ts` + `host` + snapshot JSON, indexed on `(host,ts)`). Run on a timer (Task Scheduler / cron / systemd) for long-term history. | schedule interval; `WATCHTOWER_HISTORY_DB`, `WATCHTOWER_HISTORY_RETAIN_DAYS` |
| `trends.py` | Reads `history.db` into a DataFrame for the History graph (run-count windows, host-filtered). | `METRICS`, `RUNS` |
| `search.py` | Search every logged snapshot by **component** (substring of the metric's dotted path), **computer** (host), and **date/time** (since/until). Read-only; powers the dashboard's Search box and is scriptable (`python -c "import search; search.search(component='gpu.temp', host='lab-pc')"`). | `WATCHTOWER_HISTORY_DB` |
| `notes.py` | Shared operator notes (SQLite, persistent, cross-process). Any user of the instance leaves a note the others see. Append + read only; text capped at 10 k, input validated (trust boundary). | `WATCHTOWER_NOTES_DB`, `MAX_TEXT` |

### Chat brain + retrieval

| File | Role | Key knobs |
|---|---|---|
| `brain.py` | The Ollama call. Builds the system prompt from `context.build`, POSTs to `127.0.0.1:11434/api/chat`. Read-only: the model only advises. | `MODEL="qwen2.5:32b"`, `num_ctx=32768`, `keep_alive="30m"`, `temperature=0.3`, `OLLAMA` URL |
| `context.py` | Assembles the grounding context: static facts + live snapshot (age-stamped) + findings + `RECENT TRENDS` digest + RAG references. Prefers the live cache (0-cost chat); in remote mode reads the selected host and never falls back to local collectors. | `FACTS` path |
| `rag.py` | Optional local semantic retrieval over your `.md` docs (Ollama embeddings + sqlite-vec, **hybrid vector+lexical rerank**). Read-only; degrades to silence. | `SOURCES`, `EMBED_MODEL` (default `mxbai-embed-large`), `RERANK_POOL`/`RERANK_ALPHA`, `TOP_K`, `MIN_SCORE`, `CHUNK_*` |
| `system_facts.md` | Static machine facts the chat reads every message (CPU/GPU model, normal temps, what you care about). | **edit for your box** |

### UI / CLI

| File | Role | Key knobs |
|---|---|---|
| `app.py` | Gradio web dashboard (`127.0.0.1:7860`): host selector, live stats/findings panel, chat, live graphs, History graph, **Search** accordion (by component/computer/date-time) and **Shared notes** accordion. Starts the sampler/receiver (guarded by `gr.NO_RELOAD`). | port via `WATCHTOWER_PORT` (default `7860`), default metrics/window |
| `chat.py` | CLI chat — same model + context, no web server. | — |
| `art.py` | The WATCH TOWER ASCII banner (truecolor), shared by CLI + web. | the art |

### ML core (offline tiny GPT)

| File | Role |
|---|---|
| `gpt.py` | Char tokenizer + transformer (config + attention + full model). |
| `data.py` | Synthesizes the training corpus from random snapshots (~35 % nudged hot). |
| `train.py` | Trains the GPT (`block_size=512`, ~3 min GPU to val loss ~0.19), writes `ckpt.pt` (~47 MB) + `vocab.json`. See §9 for when to retrain. |
| `infer.py` | Loads the checkpoint and generates a report from a serialized snapshot. |

### Remote / discovery

| File | Role | Key knobs |
|---|---|---|
| `ship.py` | Runs on a **monitored** machine. Streams snapshots as JSON to the dashboard/NiFi on the two-tier cadence. Stdlib only. | `ship.config.json` (host/label/tags/tiers/cadence/url) + env overrides |
| `discover.py` | Bus scan (USB/PCI via PnP, COM ports) → maps known device signatures to collectors → `--spawn` writes a stub collector for a recognized-but-uncovered device. Wired as `sysdiag.py discover`. | `DEVICE_MAP`, `_sdr_common.KNOWN` |

---

## 3. The collector contract

Every `collectors/*.py` obeys the same tiny contract — this is what makes the fleet uniform
and what you follow when writing your own:

1. **Standalone script.** It runs as its own process (`python -P collectors/foo.py`). No shared
   state, no imports from other collectors.
2. **Print exactly one JSON object, namespaced under its own key:**
   `print(json.dumps({"foo": { ... }}))`. `sysdiag.py` merges each collector's key into the
   snapshot.
3. **Degrade, never crash.** Absent hardware/subsystem → `{"foo": {"present": false}}` or a
   `{"foo": {"note": "..."}}`. Reserve `{"foo": {"error": "..."}}` for a genuinely *broken*
   data source you want surfaced — `rules.py` turns any `error` key into a WARN finding, so a
   normal "no such hardware" must **not** use `error` (that would be a permanent false warning).
4. **Bound your time.** You get ~25 s before `sysdiag` kills the subprocess. Set subprocess
   timeouts *below* that (the PowerShell collectors use `timeout=20`), and fan out if you make
   many calls.
5. **UTF-8, stdlib-first.** Decode child output `encoding="utf-8", errors="replace"` (Windows'
   cp1252 locale codec crashes on UTF-8 bytes like systemd's `●`). Prefer stdlib + already-
   installed tools (`nvidia-smi`, `wsl`, `ssh`, `powershell`) over pip deps; make any pip dep
   optional and degrade when it's missing.
6. **`_`-prefixed files are libraries, not collectors.** `sysdiag.snapshot()` skips
   `collectors/_*.py`. Shared helpers (e.g. `_sdr_common.py`) live there.

### The collectors, grouped

- **Core hardware (also the `FAST` tier):** `cpu` (load + turbo-aware clock + fastest core),
  `gpu` (util/temp/power/VRAM + throttle/PCIe/driver), `mem` (used % + commit-charge + DRAM speed),
  `sensors` (LHM tree: temps, fans/pump, **rail voltages**, **power draws**), `disk` (used % +
  **absolute free GB**).
- **Deeper hardware (full tier):** `net` (ping + gateway + DNS timing + NIC errors), `storage`
  (SMART), `whea` (**7-day-windowed** hardware errors + corrected machine-checks), `tpm`
  (via unelevated `tpmtool`), `me`, `usb`, `power` (boot forensics), `lights` (OpenRGB).
- **OS / security / diagnostics (Windows, full tier):** `os` (uptime, pending-reboot, **CPU
  microcode**, BIOS, update age, Secure Boot), `security` (Defender, firewall, VBS, BitLocker,
  failed logons), `events` (**GPU TDR resets**, app crashes, NTFS corruption, **failed scheduled
  tasks**), `procs` (top CPU/RAM/GPU-VRAM consumers), `wsl` (the WSL2 VM's RAM + vhdx size).
- **Containers / virtualization:** `docker` (running/restarting/unhealthy/exited + daemon
  reachability), `k3s` (judges `containerStatuses`, catches CrashLoopBackOff), `vm` (Hyper-V +
  encryption posture), `services` (systemd, native or via WSL), `ssh` (scrape remote Linux VMs — §8).
- **SDR skeletons (fill when hardware arrives):** `sdr`, `rx`, `tx`, `tuner`, `antenna` + the
  shared `_sdr_common.py`. They emit `present:false` today and carry `FILL-ME` blocks.

> **Windows-only collectors:** `tpm`, `me`, `os`, `security`, `events`, `wsl`. The Linux release
> omits them (the shared `rules.py` just sees no such keys) and ports `cpu`/`mem`/`disk`/`sensors`/
> `net`/`whea`/`power`/`vm`/`usb`/`storage`/`procs` to psutil/lm-sensors/journalctl — see
> `docs/RECREATE-LINUX.md`.

---

## 4. Creating & editing a collector

### 4.1 The minimal template

Create `collectors/mything.py`:

```python
# collectors/mything.py — one-line description of what it reads.
import json, subprocess

try:
    # ... read your sensor. Example: shell out to an installed tool.
    out = subprocess.run(["some-tool", "--json"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=20).stdout.strip()
    value = parse(out)
    if value is None:                       # hardware/subsystem simply not here
        print(json.dumps({"mything": {"present": False}}))
    else:
        print(json.dumps({"mything": {"present": True, "value": value}}))
except FileNotFoundError:
    print(json.dumps({"mything": {"present": False}}))   # tool absent = a state, not an error
except Exception as e:
    print(json.dumps({"mything": {"error": str(e)}}))    # a real failure worth a WARN
```

Drop it in `collectors/` and it's **live on the next snapshot** — `sysdiag.snapshot()` globs
the folder; there is no registry to edit. Test it standalone:

```
python -P collectors/mything.py
```

(Always test with `-P`: that's how `sysdiag` runs it, and it prevents your collector's filename
from shadowing a pip package it imports.)

### 4.2 Make it a finding (rules.py)

Add a rule in `rules.py`'s `diagnose()` using the `_get(snap, "mything", "value")` helper and
either the `THRESH` table (for a warn/crit number) or an explicit rule:

```python
v = _get(snap, "mything", "value")
if v is not None and v >= 100:
    out.append({"level": "WARN", "what": "my thing", "value": v, "limit": 100, "unit": ""})
```

For a numeric threshold, add `"mything_value": (warn, crit)` to `THRESH` and call the local
`chk(...)` helper instead. Add one assertion to `rules.demo()` so a regression fails loudly.

### 4.3 Put it on the live graph (live.py)

Add a label→path entry to `live.py`'s `METRICS` so it's selectable in the Live graphs:

```python
METRICS = { ... "My value": ("mything", "value"), }
```

If the value is cheap to read every 5 s, also add the collector name to `FAST` so it samples on
the fast tier; otherwise it plots at the 60 s full-tier cadence automatically (`FAST_LABELS` is
derived from `METRICS` × `FAST`).

### 4.4 Teach discovery about a device (discover.py)

If your collector covers a specific USB/PCI device, add its signature so
`python sysdiag.py discover` maps it (and `--spawn` can stub it):

```python
# discover.py DEVICE_MAP  (VID, PID-or-None) -> (collector, label)
("1234", "5678"): ("mything", "My Device"),
```

SDR signatures live in `_sdr_common.KNOWN` (shared with the `sdr`/`rx`/`tx`/`tuner`/`antenna`
collectors). `discover.py --spawn` writes a minimal stub for any recognized device with no
collector — the snapshot glob then runs it, and you fill it in.

### 4.5 Editing an existing collector

- **Preserve output keys.** `schema.serialize_metrics` reads a *frozen* set of keys
  (`cpu.load`, `sensors.cpu_temp`, `mem.pct`, `gpu.util/temp/power/vram_pct`, `disk.C`,
  `whea.recent_errors`). Never rename or drop those or you break the trained model's input.
  **Add** new keys freely.
- **Keep the degrade contract** (§3.3). Adding `error` where you meant `present:false` creates a
  permanent false WARN.
- **Windows text gotcha:** always pass `encoding="utf-8", errors="replace"` to
  `subprocess.run(..., text=True)` — the default cp1252 codec crashes on UTF-8 output.

---

## 5. Configuration reference

### 5.1 Environment variables

| Variable | Read by | Meaning | Default |
|---|---|---|---|
| `WATCHTOWER_REMOTE` | `live.py`/`app.py` | `1` = dashboard runs the HTTP receiver instead of sampling this machine | unset (local mode) |
| `WATCHTOWER_TOKEN` | receiver + `ship.py` | shared secret; the receiver **refuses to start without it** and rejects any POST whose `X-Watchtower-Token` doesn't match | — (required in remote mode) |
| `WATCHTOWER_INGEST_BIND` | receiver | `host:port` the receiver binds | `0.0.0.0:7861` |
| `WATCHTOWER_SHIP_URL` | `ship.py` | where the agent POSTs snapshots (NiFi ListenHTTP or the GUI `/ingest`) | `http://127.0.0.1:8081/watchtower` |
| `WATCHTOWER_HOST` | `ship.py` | identity of this monitored machine in the payload (overrides config `host`) | `socket.gethostname()` |
| `WATCHTOWER_SHIP_CONFIG` | `ship.py` | path to `ship.config.json` | `./ship.config.json` |
| `WATCHTOWER_SSH_CONFIG` | `ssh.py` collector | path to `ssh.config.json` | `./ssh.config.json` |
| `WATCHTOWER_PORT` | `app.py` | dashboard port (also honors `GRADIO_SERVER_PORT`) — lets a 2nd instance run alongside a local one | `7860` |
| `WATCHTOWER_HISTORY_DB` | `history.py`/`trends.py`/`search.py` | override the history SQLite path | `./history.db` |
| `WATCHTOWER_HISTORY_RETAIN_DAYS` | `history.py` | prune snapshots older than N days on each write (0 = keep all) | `0` |
| `WATCHTOWER_NOTES_DB` | `notes.py` | override the shared-notes SQLite path | `./notes.db` |
| `PYTHONIOENCODING=utf-8` | launch env | recommended when launching `app.py` so the banner + JSON print as UTF-8 on Windows | — |

### 5.2 Code-level knobs (edit the file)

| Where | Knob | Purpose |
|---|---|---|
| `rules.py` | `THRESH = {metric: (warn, crit)}` | the main per-machine tuning table (CPU/GPU/liquid temp, RAM/disk %, DNS ms, drive temp…) |
| `live.py` | `FAST_S`, `FULL_S` | fast / full sampling cadence (5 s / 60 s) |
| `live.py` | `FAST` | which collectors are cheap enough for the 5 s tier |
| `live.py` | `METRICS` | label → snapshot path for the live graphs |
| `live.py` | `SPANS` | live-graph windows (5/15/60 min) |
| `brain.py` | `MODEL` | any model you've `ollama pull`-ed |
| `brain.py` | `num_ctx` | context window (VRAM: ~256 KB/token of KV cache for a 32B) |
| `brain.py` | `keep_alive` | how long the model stays resident in VRAM |
| `brain.py` | `SYSTEM` | the assistant's instructions (advice-only, cite-the-numbers) |
| `sensors.py` | `LHM_URL` | LibreHardwareMonitor endpoint (`127.0.0.1:8085`) |
| `k3s.py` | `K3S_CMD` | how to reach kubectl (WSL distro, kubeconfig) |
| `services.py` | `systemctl_base()` | native vs `wsl systemctl` bridge (prepend `-d <distro>` if not default) |
| `collectors/ssh.py` | `BUDGET`, `PER_TARGET` | wall-clock ceiling (20 s) + per-target ssh cap (14 s) |

### 5.3 Config files

- **`ship.config.json`** (monitored machine) — identity + JSON shape + collector tiers. See §6.2.
  Copy from `ship.config.example.json`. Gitignored.
- **`ssh.config.json`** (wherever `ssh.py` runs) — remote Linux VM targets + checks. See §8.
  Copy from `ssh.config.example.json`. Gitignored.
- **`system_facts.md`** — static machine facts the chat reads. Edit for your box.

### 5.4 External prerequisites you configure

- **LibreHardwareMonitor** — Options → *Run web server* (port 8085). The only source of CPU
  temp / fan / liquid temp on Windows. (`sensors.py` also has a `liquidctl` fallback for NZXT
  AIOs; note NZXT CAM holds the pump's USB exclusively, so close CAM or let LHM read it.)
- **Ollama** — `ollama pull qwen2.5:32b` (or your chosen `MODEL`).
- **OpenRGB** (optional, for `lights.py`) — run its SDK server (port 6742).
- **OpenSSH client** (for `ssh.py`) — ships with Windows 11 / every Linux.

### 5.5 Ports

| Port | Service | Bind | When |
|---|---|---|---|
| `7860` | Gradio dashboard (`app.py`) | `127.0.0.1` | always (override with `WATCHTOWER_PORT`) |
| `7861` | Remote-ingest receiver (`live.start_receiver`) | `0.0.0.0` (override `WATCHTOWER_INGEST_BIND`) | remote mode only |
| `8081` | NiFi `ListenHTTP` (optional middle hop) | NiFi host | if routing through NiFi |
| `8085` | LibreHardwareMonitor web server | `127.0.0.1` | Windows sensors (`sensors.py`) |
| `11434` | Ollama API | `127.0.0.1` | chat brain + RAG embeddings |
| `6742` | OpenRGB SDK server | `127.0.0.1` | `lights.py` (optional) |

### 5.6 Choosing the chat-brain model (VRAM matrix)

`brain.py`'s `MODEL` is any tag you've `ollama pull`-ed; switching is one edit, same code path.
**VRAM needed ≈ model weights + KV-cache(`num_ctx`)** — pick the largest that fits with headroom
for your display/games. If it won't fit, **lower `num_ctx` before dropping model size** (grounding
quality tracks model size more than context length, because the findings are handed to the model
as ground truth regardless).

| Model | Origin | Weights | `num_ctx` | ≈VRAM | Fits |
|---|---|---|---|---|---|
| `qwen2.5:32b` **(default)** | Alibaba | ~19 GB | 32768 | ~28 GB | 32 GB |
| `gemma3:27b` | Google | ~17 GB | 16384 | ~23 GB | 24–32 GB |
| `gpt-oss:20b` | OpenAI | ~14 GB | 16384 | ~18 GB | 20–24 GB |
| `qwen2.5:14b` / `phi4` | Alibaba / Microsoft | ~9 GB | 16384 | ~12 GB | 12–16 GB |
| `qwen2.5:7b` / `llama3.1:8b` / `granite3.3:8b` | Alibaba / Meta / IBM | ~5 GB | 16384/8192 | ~7 GB | 8 GB |
| `llama3.2:3b` / `gemma3:4b` | Meta / Google | ~2–3 GB | 8192 | ~4 GB | 4–6 GB / CPU |
| `phi4-mini` / `qwen2.5:3b` | Microsoft / Alibaba | ~2 GB | 8192 | ~3 GB | CPU-ok |

The **embedding** model for RAG (§ `rag.py`) is separate and tiny — `mxbai-embed-large` (~670 MB,
measured best here) or the lighter `nomic-embed-text` (~270 MB). It only loads when RAG is used.
The full matrix with KV-cache math is in `docs/RECREATE-WINDOWS.md` §7.1.

---

## 6. Remote monitoring — one machine watches another

### 6.1 Where each piece runs

- **Collectors → the monitored machine.** They read local sensors; they can't run remotely.
- **Dashboard, rules engine, chat brain → the monitoring machine.**
- **The tiny NanoGPT narrator → either.** It's portable (no sensor dependency); `ship.py
  --narrate` runs it agent-side and ships the report text inside the JSON.

The agent side is **stdlib-only**: copy `collectors/`, `sysdiag.py`, and `ship.py` to the
monitored machine — no pip installs.

```
# on the MONITORED machine (agent)
set WATCHTOWER_SHIP_URL=http://<nifi-or-gui-host>:8081/watchtower
set WATCHTOWER_TOKEN=<shared-secret>
python ship.py            # add --narrate to also ship the NanoGPT report

# on the MONITORING machine (dashboard)
set WATCHTOWER_REMOTE=1
set WATCHTOWER_TOKEN=<shared-secret>
python app.py
```

### 6.2 `ship.config.json` — identity & JSON customization

This is where you **name the reporter** (so the dashboard can tell machines apart) and shape the
shipped JSON. Copy `ship.config.example.json`:

```jsonc
{
  "host":  "lab-pc-01",                       // identity — how the dashboard names/selects this box
  "label": "Lab PC — rack 2, GPU node",       // friendly label, shown on the panel
  "tags":  { "location": "basement", "role": "gpu-node" },   // free-form, shown on the panel
  "fast":  ["cpu", "gpu", "mem", "sensors", "disk"],  // collectors in the 5 s tier
  "full":  null,                              // 60 s tier: null = the whole fleet, or a list to restrict
  "fast_seconds": 5, "full_seconds": 60, "narrate": false,
  "url":   "http://nifi-or-gui-host:8081/watchtower"
}
```

`host` and `url` are env-overridable (`WATCHTOWER_HOST`, `WATCHTOWER_SHIP_URL`), so one shared
config file plus a per-host `WATCHTOWER_HOST=...` is enough to vary identity across machines.

### 6.3 The receiver

`WATCHTOWER_REMOTE=1` makes `app.py` run `live.start_receiver()` instead of the local sampler:
a small stdlib HTTP server (`POST /ingest`, default `0.0.0.0:7861`). It:

- **refuses to start without `WATCHTOWER_TOKEN`** and rejects any POST whose
  `X-Watchtower-Token` header doesn't match (constant-time compare), 403 otherwise;
- caps the body at 2 MB, returns clean 4xx on malformed input;
- stores each payload under a **per-host ring** keyed by the reporter's `host`.

Point `ship.py` directly at `http://<gui-host>:7861/ingest` for the no-middleman setup, or route
through NiFi (§7).

### 6.4 Multiple hosts + the host selector

Each distinct `host` gets its **own** ring, snapshot, and findings — no cross-contamination. The
dashboard's **Host** selector (top of the page) lists every reporting machine; pick one and the
stats panel, live graphs, and chat all switch to it (the chat answers about the selected host,
with that host's findings). New agents appear in the selector live. A stale feed is flagged
`STALE` rather than ever sampling the monitoring machine. Local mode is the single-host case
(keyed by this machine's hostname).

---

## 7. NiFi integration

### 7.1 Why route through NiFi

`ship.py` can POST straight to the dashboard's `/ingest`. Putting **Apache NiFi**
(https://github.com/apache/nifi) in the middle buys you, without changing any Watch Tower code:

- **Durable queueing + back-pressure** — if the dashboard is down, NiFi's queue holds the
  snapshots and retries; nothing is lost.
- **Provenance** — NiFi records the lineage of every snapshot FlowFile.
- **Fan-out** — tee the same stream to disk, Grafana, an alerting processor, etc.

### 7.2 The flow (two processors)

```
ship.py  ──HTTP POST {host,label,tags,partial,snap}──►  [ ListenHTTP ]  ──success──►  [ InvokeHTTP ]  ──►  dashboard /ingest
          X-Watchtower-Token: <secret>                    (NiFi in)                     (NiFi out)         127.0.0.1:7861
```

| Processor | Property | Value |
|---|---|---|
| **ListenHTTP** | Listening Port | `8081` |
| | Base Path | `watchtower` |
| | HTTP Headers to receive as Attributes | `X-Watchtower-Token` |
| **InvokeHTTP** | HTTP Method | `POST` |
| | Remote URL | `http://<gui-host>:7861/ingest` |
| | Request Content-Type | `application/json` |
| | Attributes to Send (regex) | `X-Watchtower-Token` |

Connect **`ListenHTTP` `success` → `InvokeHTTP`**. That's the minimal pipeline.

### 7.3 How it lines up with the code

- `ship.py` POSTs to `WATCHTOWER_SHIP_URL` = `http://<nifi-host>:8081/watchtower` — this is
  ListenHTTP's `Listening Port` + `Base Path`.
- ListenHTTP must **forward the `X-Watchtower-Token` header** (as an attribute) and InvokeHTTP
  must **send it back on** — the receiver's auth check reads that exact header. If NiFi drops it,
  every POST 403s.
- InvokeHTTP's Remote URL = the receiver's `/ingest` (`WATCHTOWER_INGEST_BIND`, default
  `:7861`).
- The JSON body passes through untouched, so per-host rings, labels, tags, and `--narrate`
  reports all work exactly as in the direct setup.

### 7.4 Fan-out example

To also archive every snapshot, add a `PutFile` (or `PutS3Object`, `PublishKafka`, …) processor
and a second connection from ListenHTTP `success` → that processor. NiFi clones the FlowFile down
both paths. The dashboard path is unaffected.

### 7.5 Security note

The token and payload ride plain HTTP — fine on a trusted LAN. If the stream crosses an
untrusted network, terminate TLS at NiFi (HTTPS on ListenHTTP) or tunnel it (WireGuard/SSH), and
bind the receiver to `127.0.0.1` (`WATCHTOWER_INGEST_BIND=127.0.0.1:7861`) when NiFi runs on the
same box as the dashboard.

---

## 8. SSH remote-VM scraper (`collectors/ssh.py`)

Scrape components on **remote Linux VMs** by SSHing in and running read-only checks — a check is
a shell command, so **reading a file is just `cat`/`grep /path`**. It shells out to the OpenSSH
client (no pip deps), opens one session per VM, and fans out with a wall-clock budget.

### 8.1 `ssh.config.json`

Copy `ssh.config.example.json` (the real file is gitignored):

```jsonc
{
  "connect_timeout": 6,
  "targets": [
    {
      "name": "db-vm",                    // shown as the target's identity
      "ssh":  "monitor@10.0.0.5",         // user@host (or "host": ...)
      "port": 22,
      "key":  "~/.ssh/id_ed25519",        // key-based auth only; passwords are disabled
      "accept_new": false,                // true = trust-on-first-use (accept-new); never "no"
      "jump": "monitor@bastion.example",  // optional ProxyJump / bastion
      "checks": {
        "disk_root_pct": { "cmd": "df --output=pcent / | tail -1 | tr -dc 0-9", "warn": 85, "crit": 95, "unit": "%" },
        "cert_days_left":{ "cmd": "...days until expiry...", "warn": 30, "crit": 7, "unit": "d" },
        "postgres":      "systemctl is-active postgresql",
        "app_debug":     "grep -c '^DEBUG=true' /etc/myapp/config.env || true"
      }
    }
  ]
}
```

### 8.2 How checks & thresholds work

- A check is either a **bare command string** or `{ "cmd": "...", "warn": N, "crit": N, "unit": "…" }`.
- The result is coerced to a number when possible; numeric results are threshold-checked into
  findings. **Direction is inferred:** `crit > warn` is higher-is-worse (disk %, load); `crit <
  warn` is lower-is-worse (cert days left, free GB) and fires when the value drops *below*.
- An **unreachable** target is a WARN. Every scraped value lands in the snapshot, so the chat can
  reason about it ("is the db VM's disk filling up?").
- The collector self-bounds to a ~20 s wall-clock budget (under the 25 s collector kill) — a hung
  VM or one bad target degrades to that one target, never the whole fleet. Scale by splitting
  configs across agents (different hosts avoid single-sshd contention).

### 8.3 Security posture (the defaults)

- **Key-based auth only** (`BatchMode`, `PasswordAuthentication=no`) — no passwords in a config
  file, no hangs on a prompt. Set up a key first (`ssh-copy-id`).
- **Host-key checking stays on** (`StrictHostKeyChecking=yes`); a new VM must be in `known_hosts`,
  or set `"accept_new": true` for trust-on-first-use (never disabled).
- Destinations/jump hosts are validated (can't pose as an ssh `-o` option); `IdentitiesOnly` +
  an explicit `-i` key; per-check output capped.
- Point checks at **read-only** commands — the collector only reads; what your commands do is
  yours to keep read-only.

---

## 9. Running & operations

### CLI chat
```
python chat.py
```
Banner, then a prompt. Ask "Is my GPU temp normal?" — grounded, step-by-step answer. `exit` frees
the model's VRAM.

### Web dashboard
```
# Windows (UTF-8 so the banner/JSON print cleanly):
$env:PYTHONIOENCODING = "utf-8"; python app.py
```
Opens `http://127.0.0.1:7860`. Host selector, live panel (5 s), chat, live graphs, History graph.
**Restart `app.py` after editing any `.py`** — Gradio caches modules.

### History logging (the History graph's + Search data)
Schedule `python history.py` every ~15 min (Windows Task Scheduler; Linux cron/systemd timer).
See the RECREATE guide for the exact `Register-ScheduledTask` / crontab line. A fresh install has
an empty History graph and Search until the logger has run a few times — seed it by running
`python history.py` several times, or wait for the schedule.

### Exit code (for scripts / CI / Task Scheduler)
`python sysdiag.py` returns a **severity exit code**: `0` = no findings, `1` = WARN only, `2` =
CRIT present (`--json` always exits `0`). So a scheduled task can alert on distress without parsing
text: e.g. `python sysdiag.py; if ($LASTEXITCODE -ge 2) { <page me> }`.

### Search & notes
Both are in the dashboard (accordions under the History graph) and scriptable:
```
python -c "import search; [print(r) for r in search.search(component='gpu.temp', host='lab-pc', since='2026-07-01T00:00:00')]"
python -c "import notes; notes.add_note('alex', 'RMA pending on the AIO pump'); print(notes.list_notes())"
```
Search matches `component` as a substring of the metric's dotted path (`cpu_temp`, `gpu`, `disk`,
`docker`…); blank fields mean *any*. Both read/write `history.db` / `notes.db` (override paths with
`WATCHTOWER_HISTORY_DB` / `WATCHTOWER_NOTES_DB`).

### Train / retrain the narrator (the tiny offline GPT)
```
python data.py 8000        # deterministic corpus (seed 1337) -> corpus.txt
python train.py            # ~3 min GPU / ~20-30 min CPU; val loss ~0.19; writes ckpt.pt (~47 MB) + vocab.json
python infer.py --demo     # INPUT / rule-truth / model-output side by side
```
`gpt.py` is ~11 M params (6 layers, 384-dim, `block_size=512`). **Retrain when** you change
`schema.serialize_metrics`, `data.render_report`, or the corpus size — the model's input/label
contract changed. You do **not** need to retrain to add collectors/rules the narrator's 10-metric
input doesn't include (those surface via the rules engine and chat brain). `corpus.txt`/`vocab.json`
/`ckpt.pt` are regenerable, git-ignored artifacts.

### Discover devices
```
python sysdiag.py discover           # list known devices → collector coverage
python sysdiag.py discover --spawn   # write a stub collector for a recognized, uncovered device
```

---

## 10. Security model (recap)

- **Read-only by design.** The chat model is told it only advises; nothing it returns is
  executed. Collectors read sensors; the SSH collector runs *your* read-only check commands.
- **Local-first, not zero-egress.** The dashboard binds `127.0.0.1:7860`; Ollama is local; no API
  keys. The one deliberate internet touch is `collectors/net.py`, which pings `1.1.1.1` and resolves
  a DNS name each full-fleet cycle to measure connectivity — delete/relax it for a truly offline
  build. Remote mode also streams snapshots to the monitoring host. Everything else stays on the box.
- **Remote ingest is authenticated** (shared token, constant-time compare, size-capped) and
  **isolated per host**. Remote snapshots are treated as semi-trusted: the rules engine is
  type-guarded so a malformed payload degrades to a finding instead of crashing the dashboard.
- **SSH is key-auth-only with host-key checking on.** Real config files (`ship.config.json`,
  `ssh.config.json`) carry topology/keys and are **gitignored** — only the `*.example.json` ship.
- Plain-HTTP ingest is for trusted LANs; add TLS/tunnel for anything else (§7.5).

---

## 11. Quick index

**Rebuild from scratch:** `docs/RECREATE-WINDOWS.md`, `docs/RECREATE-LINUX.md`.
**Add semantic doc retrieval:** RECREATE §12 (`rag.py`).
**Every collector:** `collectors/` — `cpu gpu mem sensors disk net storage whea tpm me usb power
lights docker k3s vm services ssh os security events procs wsl` + skeletons `sdr rx tx tuner
antenna` (+ `_sdr_common`).
**Tune findings:** `rules.py` `THRESH`. **Tune graphs:** `live.py` `METRICS`. **Choose the model:**
`brain.py` `MODEL`/`num_ctx` (matrix §5.6). **Train the narrator:** `data.py`→`train.py`→`infer.py`
(§9). **Search/notes:** `search.py`/`notes.py`. **Remote:** `ship.py` + `ship.config.json` +
`WATCHTOWER_*`. **SSH scrape:** `collectors/ssh.py` + `ssh.config.json`. **NiFi:** §7. **Ports:** §5.5.
