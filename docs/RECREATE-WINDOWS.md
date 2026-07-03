# Watch Tower — Recreate From Scratch (Windows)

A complete, copy-paste guide to rebuild this project on a fresh Windows machine. Every file's
full contents are included (generated from the live source by `docs/gen_recreate.py`, so they
match the code exactly), every command shows its expected output. Work top to bottom.

> Sibling guide: `RECREATE-LINUX.md`. This file is Windows-only. For a component/config *reference*
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
collectors/*.py ──► sysdiag.py ──► snapshot{json} ──► rules.py ──► findings[]
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

## 1. Prerequisites (install these first)

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
mkdir C:\Users\<you>\sysdiag; cd C:\Users\<you>\sysdiag; mkdir collectors, docs
```

---

## 3. The machine-learning core (offline tiny GPT)

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


def _i(snap, *path):
    """int() of a dug metric, but SAFE: a hostile non-numeric leaf (list/dict/str from a sick or
    spoofed remote collector) coerces to 0 instead of raising — summarize()/serialize feed the UI
    panel and the model, and must never crash on a malformed snapshot. Identical to int(_g(...))
    for the normal numeric case, so the training corpus is unchanged."""
    import math
    v = _g(snap, *path)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0
    if isinstance(v, float) and not math.isfinite(v):     # NaN/inf from a sick collector -> 0
        return 0
    return int(v)


def serialize_metrics(snap: dict) -> str:
    """The exact INPUT text the model trains and runs on. Keep it stable forever."""
    return "\n".join([
        f"cpu_load={_i(snap,'cpu','load')} cpu_temp={_i(snap,'sensors','cpu_temp')} "
        f"mem_pct={_i(snap,'mem','pct')}",
        f"gpu_util={_i(snap,'gpu','util')} gpu_temp={_i(snap,'gpu','temp')} "
        f"gpu_power={_i(snap,'gpu','power')} gpu_vram={_i(snap,'gpu','vram_pct')}",
        f"disk_C={_i(snap,'disk','C')} whea_errors={_i(snap,'whea','recent_errors')}",
    ])


def summarize(snap: dict) -> str:
    """One-line human summary embedded in every report (training label + runtime)."""
    return (f"CPU {_i(snap,'cpu','load')}% / {_i(snap,'sensors','cpu_temp')}C, "
            f"GPU {_i(snap,'gpu','util')}% / {_i(snap,'gpu','temp')}C / "
            f"{_i(snap,'gpu','power')}W, RAM {_i(snap,'mem','pct')}%, "
            f"disk C {_i(snap,'disk','C')}%.")


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


def demo():  # train/serve symmetry check: real-shaped and synthetic-shaped serialize the same way
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
    "cpu_temp":    (90, 98),   # <CPU> TjMax ~100
    "gpu_temp":    (80, 88),   # <GPU> edge
    "mem_pct":     (85, 95),
    "disk_pct":    (85, 95),
    "liquid_temp": (45, 55),   # AIO coolant; >55C the loop has lost the battle
    "drive_temp":  (70, 80),   # NVMe throttle band
    "dns_ms":      (500, 2000),  # steady-state (cached) resolve
    "dns_cold_ms": (5000, 15000),  # resolver->upstream path; this LAN has shown 11s legit-slow
    "gpu_vram":    (92, 98),   # VRAM used %; 98%+ = OOM imminent for ML work
    "commit_pct":  (85, 95),   # Windows commit charge vs limit — the REAL allocation-pressure metric
}
# absolute free-space floors (GB) — a percentage lies across drive sizes (95% of 8TB is fine,
# 95% of 256GB is not). crit < warn: LOWER is worse. A big drive with plenty of free GB is
# downgraded from a pct-CRIT to at most WARN (see the disk block).
DISK_FREE_GB = {"warn": 25, "crit": 10, "downgrade_gb": 100}
NTP_OFFSET_MS = 2000       # clock drift beyond this (either direction) is a WARN


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
        if not isinstance(value, (int, float)) or isinstance(value, bool) or lim is None:
            return                       # non-numeric (None, "N/A", a dict from a sick collector) -> no finding
        warn, crit = lim
        if value >= crit:
            out.append({"level": "CRIT", "what": label, "value": value, "limit": crit, "unit": unit})
        elif value >= warn:
            out.append({"level": "WARN", "what": label, "value": value, "limit": warn, "unit": unit})

    chk(_get(snap, "sensors", "cpu_temp"), "cpu_temp", "CPU temp")
    chk(_get(snap, "gpu", "temp"), "gpu_temp", "GPU temp")
    chk(_get(snap, "mem", "pct"), "mem_pct", "RAM", "%")

    # disk usage % — but a large drive with lots of absolute free GB is downgraded from CRIT to
    # WARN (a percentage alone lies across drive sizes). free_gb also drives its own floor rule.
    free_gb = snap.get("disk_free_gb") if isinstance(snap.get("disk_free_gb"), dict) else {}
    disk = snap.get("disk", {})
    if isinstance(disk, dict):
        warn, crit = THRESH["disk_pct"]
        for mount, pct in disk.items():
            if not isinstance(pct, (int, float)):
                continue
            gb = free_gb.get(mount)
            has_headroom = isinstance(gb, (int, float)) and gb >= DISK_FREE_GB["downgrade_gb"]
            if pct >= crit and not has_headroom:
                out.append({"level": "CRIT", "what": f"disk {mount}", "value": pct, "limit": crit, "unit": "%"})
            elif pct >= warn:
                out.append({"level": "WARN", "what": f"disk {mount}", "value": pct, "limit": warn, "unit": "%"})
    # absolute free-space floor per volume (crit < warn: lower GB is worse)
    for mount, gb in free_gb.items():
        if not isinstance(gb, (int, float)):
            continue
        if gb <= DISK_FREE_GB["crit"]:
            out.append({"level": "CRIT", "what": f"disk {mount} free space", "value": gb, "limit": DISK_FREE_GB["crit"], "unit": "GB"})
        elif gb <= DISK_FREE_GB["warn"]:
            out.append({"level": "WARN", "what": f"disk {mount} free space", "value": gb, "limit": DISK_FREE_GB["warn"], "unit": "GB"})

    # GPU VRAM pressure + commit charge — collected upstream, never previously thresholded
    chk(_get(snap, "gpu", "vram_pct"), "gpu_vram", "GPU VRAM", "%")
    chk(_get(snap, "mem", "commit_pct"), "commit_pct", "commit charge", "%")

    # WHEA / hardware errors -> straight to CRIT (no threshold; any is bad)
    whea = _get(snap, "whea", "recent_errors")
    if whea:
        out.append({"level": "CRIT", "what": "WHEA hardware errors", "value": whea, "limit": "", "unit": ""})

    # cooling rule (a rule, not a reading): hot AND the fan that matters is stalled.
    # Unpopulated headers legitimately read 0 RPM forever, so judge only the CPU fan(s) —
    # or a total stall (every reported fan at 0).
    cpu_temp = _get(snap, "sensors", "cpu_temp")
    if not isinstance(cpu_temp, (int, float)) or isinstance(cpu_temp, bool):
        cpu_temp = None                             # hostile/absent -> don't compare a dict to 90
    fans = _get(snap, "sensors", "fans")
    fans = fans if isinstance(fans, dict) else {}   # remote JSON may send a non-dict; don't crash
    cpu_fans = {k: v for k, v in fans.items()
                if "cpu" in str(k).lower() and isinstance(v, (int, float))}
    numeric = [v for v in fans.values() if isinstance(v, (int, float))]
    if cpu_temp and cpu_temp >= 90 and numeric and (
            (cpu_fans and min(cpu_fans.values()) == 0) or max(numeric) == 0):
        out.append({"level": "CRIT", "what": "cooling (hot + stalled fan)", "value": cpu_temp, "limit": "", "unit": "C"})

    # liquid cooling: coolant temp + pump-stalled-while-warm
    liquid = _get(snap, "sensors", "liquid_temp")
    chk(liquid, "liquid_temp", "coolant temp")
    pump = _get(snap, "sensors", "pump_rpm")
    if isinstance(liquid, (int, float)) and not isinstance(liquid, bool) and liquid >= 45 and pump == 0:
        out.append({"level": "CRIT", "what": "AIO pump (stalled while coolant warm)",
                    "value": 0, "limit": "", "unit": "RPM"})

    # GPU throttling: thermal/hardware slowdowns are findings; sw_power_cap at load is normal
    throttle = _get(snap, "gpu", "throttle") or []
    hard = [r for r in throttle if r in ("hw_thermal", "hw_slowdown", "hw_power_brake")]
    soft = [r for r in throttle if r == "sw_thermal"]
    if hard:
        out.append({"level": "CRIT", "what": "GPU hardware slowdown", "value": ",".join(hard), "limit": "", "unit": ""})
    elif soft:
        out.append({"level": "WARN", "what": "GPU thermal throttling", "value": ",".join(soft), "limit": "", "unit": ""})

    # PCIe link degraded — judged only under load (idle legitimately downshifts gen AND width)
    util = _get(snap, "gpu", "util") or 0
    pcie = _get(snap, "gpu", "pcie") or {}
    if util >= 30 and pcie.get("gen") and pcie.get("gen_max") and (
            pcie["gen"] < pcie["gen_max"] or (pcie.get("width") or 0) < (pcie.get("width_max") or 0)):
        out.append({"level": "WARN", "what": "PCIe link degraded under load",
                    "value": f"gen{pcie['gen']}x{pcie.get('width')}",
                    "limit": f"gen{pcie['gen_max']}x{pcie.get('width_max')}", "unit": ""})

    # storage depth: error totals, drive temps, disk-subsystem event noise
    for d in _get(snap, "storage", "drives") or []:
        if not isinstance(d, dict):     # PS 5.1 wraps an empty pipeline as [null]
            continue
        errs = (d.get("read_errs") or 0) + (d.get("write_errs") or 0)
        if errs:
            out.append({"level": "WARN", "what": f"drive errors ({d.get('name')})",
                        "value": errs, "limit": "", "unit": ""})
        chk(d.get("temp"), "drive_temp", f"drive temp ({d.get('name')})")
    ev = _get(snap, "storage", "disk_events_24h")
    if ev:
        out.append({"level": "WARN", "what": "disk error events (24h)", "value": ev, "limit": "", "unit": ""})

    # power forensics: the machine died without a clean shutdown / firmware throttled the CPU
    dirty = max(_get(snap, "power", "dirty_reboots_7d") or 0,
                _get(snap, "power", "unexpected_shutdowns_7d") or 0)
    if dirty:
        out.append({"level": "CRIT" if dirty >= 3 else "WARN",
                    "what": "dirty shutdowns (7d)", "value": dirty, "limit": "", "unit": ""})
    thr = _get(snap, "power", "cpu_throttle_events_24h")
    if thr:
        out.append({"level": "WARN", "what": "CPU throttle events (24h)", "value": thr, "limit": "", "unit": ""})

    # systemd: a failed unit is a clear signal; name the units so the fix is obvious
    failed = _get(snap, "services", "failed")
    if failed:
        units = _get(snap, "services", "failed_units") or []
        names = ", ".join(str(u) for u in units[:5]) if isinstance(units, list) else ""
        out.append({"level": "CRIT" if failed >= 3 else "WARN", "what": "failed services",
                    "value": names or failed, "limit": "", "unit": ""})

    # remote SSH-scraped VMs: unreachable target -> WARN; each check carries its own thresholds.
    # Fully type-guarded: this block sees semi-trusted JSON from a monitored box over the remote
    # ingest path, so a malformed checks/warn/crit must not crash diagnose().
    ssh_targets = _get(snap, "ssh", "targets")
    if isinstance(ssh_targets, dict):
        for tname, t in ssh_targets.items():
            if not isinstance(t, dict):
                continue
            if t.get("reachable") is False:
                out.append({"level": "WARN", "what": f"SSH target unreachable ({tname})",
                            "value": t.get("error", "no reply"), "limit": "", "unit": ""})
                continue
            checks = t.get("checks")
            if not isinstance(checks, dict):
                continue
            for cname, c in checks.items():
                if not isinstance(c, dict) or not isinstance(c.get("value"), (int, float)):
                    continue
                v = c["value"]
                warn = c["warn"] if isinstance(c.get("warn"), (int, float)) else None
                crit = c["crit"] if isinstance(c.get("crit"), (int, float)) else None
                unit = c.get("unit", "")
                # direction inferred from the thresholds: crit < warn means lower-is-worse
                # (cert days left, free GB) -> fire when value drops BELOW; else higher-is-worse.
                low = warn is not None and crit is not None and crit < warn
                hit = (lambda th: v <= th) if low else (lambda th: v >= th)
                if crit is not None and hit(crit):
                    out.append({"level": "CRIT", "what": f"{tname}:{cname}", "value": v, "limit": crit, "unit": unit})
                elif warn is not None and hit(warn):
                    out.append({"level": "WARN", "what": f"{tname}:{cname}", "value": v, "limit": warn, "unit": unit})

    # NIC errors + sick resolver (cached lookups slow = resolver itself is unhealthy)
    nic_errs = (_get(snap, "net", "rx_errors") or 0) + (_get(snap, "net", "tx_errors") or 0)
    if nic_errs:
        out.append({"level": "WARN", "what": "NIC packet errors", "value": nic_errs, "limit": "", "unit": ""})
    chk(_get(snap, "net", "dns_ms"), "dns_ms", "DNS resolve", "ms")
    chk(_get(snap, "net", "dns_cold_ms"), "dns_cold_ms", "DNS cold resolve", "ms")
    # resolver DEAD (dns_ms None while raw-IP ping works) = "internet up but nothing loads"
    if "net" in snap and _get(snap, "net", "dns_ms") is None and _get(snap, "net", "ping_ms") is not None:
        out.append({"level": "CRIT", "what": "DNS resolution (ping OK, resolve fails)",
                    "value": "no answer", "limit": "", "unit": ""})

    # internet down
    if "net" in snap and _get(snap, "net", "ping_ms") is None:
        out.append({"level": "CRIT", "what": "internet (1.1.1.1)", "value": "no reply", "limit": "", "unit": ""})

    # containers (Docker): a restart-looping / unhealthy / exited container is a real finding —
    # 'running < total' alone is NOT (a container you stopped on purpose is not a fault).
    docker = _get(snap, "docker")
    if isinstance(docker, dict) and "error" not in docker:
        if docker.get("daemon_ok") is False:
            out.append({"level": "CRIT", "what": "docker daemon", "value": "unreachable", "limit": "", "unit": ""})
        restarting = docker.get("restarting")
        if isinstance(restarting, (int, float)) and not isinstance(restarting, bool) and restarting >= 1:
            out.append({"level": "WARN", "what": "docker containers restart-looping", "value": int(restarting), "limit": "", "unit": ""})
        unhealthy = docker.get("unhealthy")
        if isinstance(unhealthy, (int, float)) and not isinstance(unhealthy, bool) and unhealthy >= 1:
            out.append({"level": "WARN", "what": "docker containers unhealthy", "value": int(unhealthy), "limit": "", "unit": ""})
        # only NON-ZERO exits (crashes) are a finding — a container you stopped on purpose
        # ("Exited (0)") is not a fault. Read exited_bad specifically (not the total `exited`,
        # which counts clean stops); absent on a legacy agent -> no finding, which is correct.
        exited_bad = docker.get("exited_bad")
        if isinstance(exited_bad, (int, float)) and not isinstance(exited_bad, bool) and exited_bad >= 1:
            out.append({"level": "WARN", "what": "docker containers crashed", "value": int(exited_bad), "limit": "", "unit": ""})

    # k3s: phase='Running' hides CrashLoopBackOff and not-ready containers — judge those explicitly
    k3s = _get(snap, "k3s")
    if isinstance(k3s, dict) and "error" not in k3s:
        cl = k3s.get("crashloop")
        if isinstance(cl, (int, float)) and not isinstance(cl, bool) and cl >= 1:
            out.append({"level": "WARN", "what": "k3s pods crash-looping", "value": int(cl), "limit": "", "unit": ""})
        nr = k3s.get("not_ready")
        if isinstance(nr, (int, float)) and not isinstance(nr, bool) and nr >= 1:
            out.append({"level": "WARN", "what": "k3s pods not ready", "value": int(nr), "limit": "", "unit": ""})

    # corrected machine-checks: not (yet) failures, but a rising count is the early-warning of a
    # dying part — surfaced as WARN, separate from the straight-to-CRIT uncorrected WHEA above.
    corrected = _get(snap, "whea", "corrected_7d")
    if isinstance(corrected, (int, float)) and not isinstance(corrected, bool) and corrected >= 1:
        out.append({"level": "WARN", "what": "corrected machine-checks (7d)", "value": int(corrected), "limit": "", "unit": ""})

    # GPU driver resets (WDDM TDR / Event 4101) — the canonical GPU-instability signal on Windows
    tdr = _get(snap, "events", "gpu_tdr_7d")
    if isinstance(tdr, (int, float)) and not isinstance(tdr, bool) and tdr >= 1:
        out.append({"level": "WARN", "what": "GPU driver resets (TDR, 7d)", "value": int(tdr), "limit": "", "unit": ""})

    # scheduled tasks whose last run failed (history.py itself runs from Task Scheduler)
    tasks = _get(snap, "events", "task_failures")
    if isinstance(tasks, list) and tasks:
        names = ", ".join(str(t) for t in tasks[:5])
        out.append({"level": "WARN", "what": "scheduled task failures", "value": names, "limit": "", "unit": ""})

    # drive health -> imminent failure. Two signals: an explicit SMART critical-warning flag
    # (smartctl exposes it on Linux), OR the collected HealthStatus (Get-PhysicalDisk on Windows,
    # smartctl on Linux) reading a bad value. The original rule only checked smart_critical_warning,
    # which the Windows/Linux storage collectors never emit -> it was dead. `health` is what they
    # actually report, so judge that too (allow-list of BAD values so an "Unknown"/null never fires).
    _BAD_HEALTH = {"warning", "unhealthy", "failed", "bad", "caution", "degraded", "pred fail"}
    for d in _get(snap, "storage", "drives") or []:
        if not isinstance(d, dict):
            continue
        if d.get("smart_critical_warning") is True:
            out.append({"level": "CRIT", "what": f"SMART critical warning ({d.get('name')})", "value": "set", "limit": "", "unit": ""})
        h = str(d.get("health") or "").strip().lower()
        if h in _BAD_HEALTH:
            out.append({"level": "CRIT", "what": f"drive health ({d.get('name')})", "value": d.get("health"), "limit": "", "unit": ""})

    # OS posture: a pending reboot leaves patches half-applied; clock drift breaks logs/certs/auth
    if _get(snap, "os", "pending_reboot") is True:
        out.append({"level": "WARN", "what": "reboot pending", "value": "yes", "limit": "", "unit": ""})
    ntp = _get(snap, "os", "ntp_offset_ms")
    if isinstance(ntp, (int, float)) and not isinstance(ntp, bool) and abs(ntp) >= NTP_OFFSET_MS:
        out.append({"level": "WARN", "what": "system clock drift", "value": int(ntp), "limit": NTP_OFFSET_MS, "unit": "ms"})

    # security posture: real-time AV off is a genuine exposure worth a finding
    if _get(snap, "security", "defender_on") is False:
        out.append({"level": "WARN", "what": "Windows Defender real-time protection off", "value": "disabled", "limit": "", "unit": ""})

    # any collector that returned {"error": ...} is itself a (low-sev) finding
    for k, v in snap.items():
        if isinstance(v, dict) and "error" in v:
            out.append({"level": "WARN", "what": f"{k} sensor", "value": v["error"], "limit": "", "unit": ""})

    # a collector that died outright (timeout/bad JSON) must surface too, not vanish
    for msg in snap.get("_errors") or []:
        out.append({"level": "WARN", "what": "collector failed", "value": msg, "limit": "", "unit": ""})

    return out


def demo():  # the one runnable check: a hot GPU MUST raise CRIT
    hot = {"gpu": {"temp": 99}, "net": {"ping_ms": 12}, "whea": {"recent_errors": 0}}
    assert any(f["level"] == "CRIT" for f in diagnose(hot)), "rule engine broken"
    stalled = {"sensors": {"liquid_temp": 48, "pump_rpm": 0}}
    assert any("pump" in f["what"] for f in diagnose(stalled)), "pump rule broken"
    idle_pcie = {"gpu": {"util": 3, "pcie": {"gen": 1, "gen_max": 5, "width": 8, "width_max": 16}}}
    assert not any("PCIe" in f["what"] for f in diagnose(idle_pcie)), "idle PCIe must not flag"
    loaded_pcie = {"gpu": {"util": 95, "pcie": {"gen": 1, "gen_max": 5, "width": 8, "width_max": 16}}}
    assert any("PCIe" in f["what"] for f in diagnose(loaded_pcie)), "loaded PCIe must flag"
    throttling = {"gpu": {"throttle": ["hw_thermal"]}}
    assert any(f["level"] == "CRIT" and "slowdown" in f["what"] for f in diagnose(throttling)), "throttle rule broken"
    bad_drive = {"storage": {"drives": [None, {"name": "X", "read_errs": 3, "write_errs": 0}]}}
    assert any("drive errors" in f["what"] for f in diagnose(bad_drive)), "drive-error rule broken (or [null] crash)"
    dead_dns = {"net": {"ping_ms": 12, "dns_ms": None}}
    assert any("DNS resolution" in f["what"] for f in diagnose(dead_dns)), "dead-resolver rule broken"
    unpopulated = {"sensors": {"cpu_temp": 95, "fans": {"CPU Fan": 1500, "System Fan #5": 0}}}
    assert not any("cooling" in f["what"] for f in diagnose(unpopulated)), "empty header must not CRIT"
    died = {"_errors": ["net.py: timeout"]}
    assert any("collector failed" in f["what"] for f in diagnose(died)), "_errors must surface"
    svc = {"services": {"failed": 2, "failed_units": ["nginx.service", "sshd.service"]}}
    assert any("failed services" in f["what"] and "nginx" in str(f["value"]) for f in diagnose(svc)), "service rule broken"
    ssh_snap = {"ssh": {"targets": {
        "db-vm": {"reachable": True, "checks": {
            "disk_root_pct": {"value": 96, "warn": 85, "crit": 95, "unit": "%"},   # high-is-worse
            "cert_days_left": {"value": 3, "warn": 30, "crit": 7, "unit": "d"}}},   # low-is-worse
        "web-vm": {"reachable": False, "error": "timeout"}}}}
    sf = diagnose(ssh_snap)
    assert any(f["level"] == "CRIT" and "db-vm:disk_root_pct" in f["what"] for f in sf), "ssh high threshold broken"
    assert any(f["level"] == "CRIT" and "db-vm:cert_days_left" in f["what"] for f in sf), "ssh low-is-worse broken"
    assert any("unreachable (web-vm)" in f["what"] for f in sf), "ssh unreachable rule broken"
    # a healthy cert (many days left) must NOT fire, and malformed remote input must not crash
    assert not any("cert" in f["what"] for f in diagnose({"ssh": {"targets": {"x": {"reachable": True,
        "checks": {"cert_days_left": {"value": 90, "warn": 30, "crit": 7}}}}}})), "healthy cert false-fired"
    for bad in ([1, 2, 3], "pwn", 5):
        diagnose({"ssh": {"targets": {"x": {"reachable": True, "checks": bad}}}})       # no crash
    diagnose({"ssh": {"targets": {"x": {"reachable": True, "checks": {"c": {"value": 9, "crit": "x"}}}}}})
    # new rules (run 1): containers, VRAM/commit, free-GB floor + big-drive downgrade, OS/security
    assert any("restart-looping" in f["what"] for f in diagnose({"docker": {"restarting": 2}})), "docker restart rule"
    assert not any("docker" in f["what"] for f in diagnose({"docker": {"running": 44, "total": 44, "restarting": 0, "unhealthy": 0, "exited": 0}})), "healthy docker must be silent"
    assert any("crash-looping" in f["what"] for f in diagnose({"k3s": {"crashloop": 1}})), "k3s crashloop rule"
    assert any(f["level"] == "CRIT" and "VRAM" in f["what"] for f in diagnose({"gpu": {"vram_pct": 99}})), "vram rule"
    assert not any("VRAM" in f["what"] for f in diagnose({"gpu": {"vram_pct": "N/A"}})), "non-numeric vram must not crash/fire"
    dfree = diagnose({"disk": {"E": 96}, "disk_free_gb": {"E": 350}})
    assert any(f["level"] == "WARN" and f["what"] == "disk E" for f in dfree) and not any(f["level"] == "CRIT" and f["what"] == "disk E" for f in dfree), "big-drive downgrade"
    assert any(f["level"] == "CRIT" and "free space" in f["what"] for f in diagnose({"disk_free_gb": {"C": 8}})), "free-GB floor"
    assert any("clock drift" in f["what"] for f in diagnose({"os": {"ntp_offset_ms": 5000}})), "clock drift rule"
    assert not any("reboot" in f["what"] for f in diagnose({"os": {"pending_reboot": None}})), "None reboot must not fire"
    for bad in ("pwn", [1, 2, 3], 5):
        diagnose({"docker": bad}); diagnose({"k3s": bad})     # hostile types must not crash
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
block_size   = 512     # >= the longest training doc (max 434 chars) so a multi-finding report is
#                        generated with its INPUT metrics still in the attention window (was 256,
#                        which truncated ~10% of alert docs mid-report). See RSI run 7.
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

## 4. The collectors (live sensors)

Each is a standalone script that prints one namespaced JSON object and **degrades** (never crashes) when its hardware/subsystem is absent. Create `collectors/` and add each file.

### `collectors/cpu.py`

Core counts + live load + true current clock (turbo-aware) + fastest single-core clock.

```python
# collectors/cpu.py — core counts (CIM) + live load + REAL current clock. Win32_Processor's
# CurrentClockSpeed sticks at base clock on modern Windows, so the true clock is
# MaxClockSpeed * '% Processor Performance' (which runs >100% under turbo). Temp: sensors.py.
import json, subprocess
ps = (r"$c=Get-CimInstance Win32_Processor;"
      # modern counter first (Task Manager semantics; survives legacy-counter corruption),
      # legacy fallback, else an HONEST null — never a fabricated 0
      r"$l=(Get-Counter '\Processor Information(_Total)\% Processor Utility' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue;"
      r"if($null -eq $l){$l=(Get-Counter '\Processor(_Total)\% Processor Time' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue};"
      # final fallback: Win32_Processor.LoadPercentage is locale-INDEPENDENT, so `load` (which
      # feeds the frozen model input) is never null just because the perf-counter NAMES are
      # localized on a non-English Windows.
      r"if($null -eq $l){$l=(Get-CimInstance Win32_Processor -EA SilentlyContinue|"
      r"Measure-Object LoadPercentage -Average).Average};"
      r"$load=if($null -ne $l){[math]::Min(100,[int]$l)}else{$null};"
      r"$perf=(Get-Counter '\Processor Information(_Total)\% Processor Performance' "
      r"-EA SilentlyContinue).CounterSamples.CookedValue;"
      r"$max=($c.MaxClockSpeed|Measure-Object -Maximum).Maximum;"
      r"$cur=if($perf){[int]($max*$perf/100)}else{$null};"
      # per-core % Processor Performance -> the fastest single core right now (hybrid P-cores
      # boost well past the fleet average, which sits below base under mixed load)
      r"$pc=(Get-Counter '\Processor Information(*)\% Processor Performance' -EA SilentlyContinue)."
      r"CounterSamples|Where-Object{$_.InstanceName -notmatch '_Total'};"
      r"$pk=if($pc){($pc.CookedValue|Measure-Object -Maximum).Maximum}else{$null};"
      r"$maxcore=if($pk){[int]($max*$pk/100)}else{$null};"
      r"[pscustomobject]@{cores=($c.NumberOfCores|Measure-Object -Sum).Sum;"
      r"logical=($c.NumberOfLogicalProcessors|Measure-Object -Sum).Sum;load=$load;"
      r"mhz=$cur;max_core_mhz=$maxcore;base_mhz=$max}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"cpu": {"cores": d["cores"], "logical": d["logical"], "load": d["load"],
                              "mhz": d.get("mhz"), "max_core_mhz": d.get("max_core_mhz"),
                              "base_mhz": d.get("base_mhz")}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))
```

### `collectors/mem.py`

RAM used %, per-DIMM inventory, commit-charge % (the real allocation-pressure metric), DRAM speed.

```python
# collectors/mem.py — physical RAM used %, per-DIMM inventory, AND commit charge % (the real
# Windows allocation-pressure metric — a box at 60% physical can still be failing allocations
# with commit exhausted) + configured DRAM speed. PartNumber is coerced through a string so a
# null (VMs / soldered RAM) doesn't drop the whole DIMM via .Trim() on $null.
import json, subprocess
ps = (r"$o=Get-CimInstance Win32_OperatingSystem;"
      r"$used=[math]::Round(100*($o.TotalVisibleMemorySize-$o.FreePhysicalMemory)/$o.TotalVisibleMemorySize);"
      # commit charge = (commit limit - free commit) / commit limit; from the OS virtual-memory
      # counters (TotalVirtualMemorySize is the commit LIMIT in KB). No perf counter needed.
      r"$commit=if($o.TotalVirtualMemorySize){[math]::Round(100*($o.TotalVirtualMemorySize-$o.FreeVirtualMemory)/$o.TotalVirtualMemorySize,1)}else{$null};"
      r"$dimms=Get-CimInstance Win32_PhysicalMemory | ForEach-Object {"
      r"[pscustomobject]@{slot=$_.DeviceLocator;gb=[math]::Round($_.Capacity/1GB);"
      r"speed=$_.Speed;configured=$_.ConfiguredClockSpeed;part=([string]$_.PartNumber).Trim()}};"
      r"$cfg=($dimms|Where-Object configured|Select-Object -First 1).configured;"
      r"[pscustomobject]@{pct=$used;commit_pct=if($commit){[math]::Round($commit,1)}else{$null};"
      r"dram_mhz=$cfg;dimms=@($dimms)}|ConvertTo-Json -Compress -Depth 4")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    dimms = d["dimms"] if isinstance(d["dimms"], list) else [d["dimms"]]
    print(json.dumps({"mem": {"pct": d["pct"], "commit_pct": d.get("commit_pct"),
                              "dram_mhz": d.get("dram_mhz"), "dimms": dimms}}))
except Exception as e:
    print(json.dumps({"mem": {"error": str(e)}}))
```

### `collectors/disk.py`

Used % AND absolute free GB per fixed drive (free GB lets rules downgrade a big-drive pct-CRIT).

```python
# collectors/disk.py — used% AND absolute free GB per fixed drive, pure stdlib (no PowerShell,
# no pip). free GB matters because a percentage lies across drive sizes: 95% of an 8TB drive
# (400GB free) is fine for months, 95% of a 256GB system disk (12GB free) is imminent failure —
# rules.py uses disk_free_gb to downgrade a big-drive pct-CRIT to a WARN.
import json, os, shutil, string

used, free = {}, {}
for letter in string.ascii_uppercase:
    root = f"{letter}:\\"
    if os.path.exists(root):
        try:
            u = shutil.disk_usage(root)
            used[letter] = round(100 * u.used / u.total)
            free[letter] = round(u.free / 1024**3, 1)      # GB
        except OSError:
            pass  # empty card reader / disconnected drive: skip
print(json.dumps({"disk": used, "disk_free_gb": free}))
```

### `collectors/gpu.py`

nvidia-smi: util/temp/power/VRAM + fan %, P-state, clocks, PCIe link gen/width, throttle reasons, driver.

```python
# collectors/gpu.py — nvidia-smi deep query (ships with the driver, zero pip):
# util/temp/power/vram (frozen keys) + fan %, P-state, SM clock vs max, power limit,
# PCIe link gen/width current-vs-max, and decoded throttle reasons. Absent GPU -> degrades.
import json, subprocess, shutil
smi = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"

THROTTLE = {0x1: "idle", 0x2: "app_clocks", 0x4: "sw_power_cap", 0x8: "hw_slowdown",
            0x10: "sync_boost", 0x20: "sw_thermal", 0x40: "hw_thermal",
            0x80: "hw_power_brake", 0x100: "display_clocks"}


def q(fields):
    # 7s x up-to-3 calls = 21s worst case, safely under sysdiag's 25s kill switch
    r = subprocess.run([smi, f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=7)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError((r.stderr or r.stdout).strip()[:200] or f"nvidia-smi rc={r.returncode}")
    return [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")]


def num(x):  # "[N/A]" / "N/A" / "" -> None
    try:
        return float(x)
    except ValueError:
        return None


def i(x):
    n = num(x)
    return None if n is None else int(n)


try:
    (u, t, p, used, total, fan, pstate, sm, smmax,
     gen, genmax, w, wmax, plim) = q(
        "utilization.gpu,temperature.gpu,power.draw,memory.used,memory.total,"
        "fan.speed,pstate,clocks.sm,clocks.max.sm,pcie.link.gen.current,pcie.link.gen.max,"
        "pcie.link.width.current,pcie.link.width.max,power.limit")
    reasons = None
    for f in ("clocks_event_reasons.active", "clocks_throttle_reasons.active"):
        try:                                       # field renamed across driver generations
            mask = int(q(f)[0], 16)
            reasons = [n for b, n in THROTTLE.items() if mask & b and n != "idle"]
            break
        except Exception:
            continue
    vram = round(100 * num(used) / num(total)) if num(used) is not None and num(total) else None
    driver = None
    try:
        driver = q("driver_version")[0] or None
    except Exception:
        pass
    print(json.dumps({"gpu": {
        "util": i(u), "temp": i(t), "power": i(p), "vram_pct": vram,
        "vram_used_mb": i(used), "vram_total_mb": i(total),
        "fan_pct": i(fan), "pstate": pstate, "sm_mhz": i(sm), "sm_max_mhz": i(smmax),
        "power_limit": i(plim), "throttle": reasons, "driver": driver,
        "pcie": {"gen": i(gen), "gen_max": i(genmax), "width": i(w), "width_max": i(wmax)},
    }}))
except FileNotFoundError:
    print(json.dumps({"gpu": {"present": False}}))  # no NVIDIA driver at all: a state, not an error
except Exception as e:
    msg = str(e)
    if "No devices were found" in msg or "couldn't communicate" in msg:
        print(json.dumps({"gpu": {"present": False}}))
    else:
        print(json.dumps({"gpu": {"error": msg}}))  # driver present but sick = a real finding
```

### `collectors/sensors.py`

Reads LibreHardwareMonitor's whole tree (all temps incl. AIO liquid, fans + pump, rail voltages, power draws); `liquidctl` fallback for the AIO when LHM is down.

```python
# collectors/sensors.py — LibreHardwareMonitor web JSON: the WHOLE tree (every temp —
# CPU/VRM/chipset/NVMe/GPU hotspot — every fan and pump RPM), plus liquid/coolant temp.
# AIO fallback: if LHM doesn't surface a liquid temp, try liquidctl (optional dep).
# NOTE: NZXT CAM holds the Kraken's HID exclusively — liquidctl reads work when CAM is
# closed, or run LHM (it reads the Kraken too) and this collector gets it from data.json.
import json, re, os, sys, urllib.request
# our sibling usb.py/power.py would shadow pip packages (liquidctl imports pyusb as
# `usb`) — drop this script's own dir from sys.path before any third-party import
sys.path = [p for p in sys.path
            if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
LHM_URL = "http://127.0.0.1:8085/data.json"
CATEGORIES = {"Temperatures", "Fans", "Voltages", "Powers", "Clocks", "Load", "Loads",
              "Controls", "Levels", "Data", "Rates", "Throughput", "Factors", "Times"}


def walk(node, temps, fans, volts, powers, hw=""):
    name, val = node.get("Text", ""), node.get("Value", "")
    m = re.match(r"\s*(-?\d+(?:[.,]\d+)?)\s*(\S+)?", val) if val else None
    if m:
        num, unit = float(m.group(1).replace(",", ".")), (m.group(2) or "")
        key = f"{hw}: {name}" if hw else name
        if unit.endswith("C"):
            temps[key] = num
        elif unit == "RPM":
            fans[key] = int(num)
        elif unit == "V":                        # rail voltages: 12V/5V/Vcore sag = PSU warning
            volts[key] = num
        elif unit == "W":                        # CPU package / GPU board power
            powers[key] = num
    kids = node.get("Children", [])
    if kids and not m and name and name not in CATEGORIES:
        hw = name                                # nearest hardware node names the sensor
    for ch in kids:
        walk(ch, temps, fans, volts, powers, hw)


def pick(d, *words):  # first value whose key contains ALL words (case-insensitive)
    for k, v in d.items():
        if all(w in k.lower() for w in words):
            return v
    return None


def liquidctl_read():  # (liquid_temp, pump_rpm, note) — degrades to (None, None, reason)
    try:
        from liquidctl import find_liquidctl_devices
    except ImportError:
        return None, None, None
    for dev in find_liquidctl_devices():
        try:
            with dev.connect():
                st = {k.lower(): v for k, v, _ in dev.get_status()}
                liq = pick(st, "liquid") or pick(st, "coolant") or pick(st, "water")
                pump = pick(st, "pump", "speed") or pick(st, "pump", "rpm")
                return liq, pump, None
        except Exception as e:
            return None, None, (f"{dev.description}: read blocked ({type(e).__name__}) "
                                "— close NZXT CAM or run LibreHardwareMonitor")
    return None, None, None


temps, fans, volts, powers, lhm_err = {}, {}, {}, {}, None
try:
    with urllib.request.urlopen(LHM_URL, timeout=3) as r:
        walk(json.loads(r.read().decode("utf-8", "replace")), temps, fans, volts, powers)
except Exception as e:
    lhm_err = f"LHM not reachable: {e}"

cpu_matches = ([v for k, v in temps.items() if "cpu" in k.lower() and "package" in k.lower()]
               or [v for k, v in temps.items() if "cpu" in k.lower()])
liquid = pick(temps, "liquid") or pick(temps, "coolant") or pick(temps, "water")
pump = pick(fans, "pump")
if pump == 0 and liquid is None:
    pump = None      # 0-RPM 'Pump Fan' with no liquid temp = unpopulated mobo header, not the AIO
aio_note = None
if liquid is None:
    liquid, pump2, aio_note = liquidctl_read()
    pump = pump if pump is not None else pump2

out = {"cpu_temp": int(max(cpu_matches)) if cpu_matches else None,
       "fans": fans, "temps": temps, "voltages": volts, "powers": powers,
       "liquid_temp": liquid, "pump_rpm": pump}
if aio_note:
    out["aio_note"] = aio_note
if lhm_err:
    out["error"] = lhm_err                      # keeps the existing LHM-down WARN finding
print(json.dumps({"sensors": out}))
```

### `collectors/net.py`

Ping 1.1.1.1 + gateway (LAN-vs-WAN fault isolation), NIC error counters, cold/warm DNS timing, resolver in use.

```python
# collectors/net.py — ping 1.1.1.1 (stdlib) + link state + NIC error/discard counters
# (Get-NetAdapterStatistics) + DNS resolve time (stdlib; catches a dead/slow Pi-hole
# even when raw IP ping is fine — the classic "internet up but nothing loads").
import json, subprocess, re, platform, socket, time, threading


def ping(host="1.1.1.1", timeout=5):
    n = "-n" if platform.system() == "Windows" else "-c"
    # bound the ICMP wait itself (-w ms on Windows, -W s on Linux) so a dead host returns fast —
    # the gateway ping runs AFTER the concurrent probes join, so it must not add ~5s and risk
    # tripping sysdiag's 25s collector kill.
    w = ["-w", str(timeout * 1000)] if platform.system() == "Windows" else ["-W", str(timeout)]
    try:
        out = subprocess.run(["ping", n, "1", *w, host], capture_output=True, text=True,
                             timeout=timeout + 1).stdout
        m = re.search(r"time[=<]\s*(\d+)\s*ms", out)   # "time=12ms" / "time<1ms"
        return int(m.group(1)) if m else None
    except Exception:
        return None


def dns_ms(name="example.com", wait=13.0):
    # getaddrinfo has no timeout knob and a dead resolver stalls it ~10-12s per call,
    # which would blow sysdiag's 25s kill switch — so bound it with a daemon thread.
    # wait=13 clears this LAN's measured worst legit cold resolve (~11s via Pi-hole).
    res = {}

    def _resolve():
        t0 = time.perf_counter()
        try:
            socket.getaddrinfo(name, 443)
            res["ms"] = int((time.perf_counter() - t0) * 1000)
        except OSError:
            res["ms"] = None                          # resolution failing IS the signal
    th = threading.Thread(target=_resolve, daemon=True)
    th.start()
    th.join(wait)
    return res.get("ms")                              # still running -> None (resolver sick)


def dns_pair():
    # cold exercises the resolver->upstream path, warm the cache; skip warm if cold hung
    cold = dns_ms()
    warm = dns_ms(wait=6.0) if cold is not None else None
    return cold, warm


def link():
    ps = (r"$a=Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | Select-Object -First 1;"
          r"$s=$a | Get-NetAdapterStatistics -EA SilentlyContinue;"
          r"$gw=(Get-NetRoute -DestinationPrefix '0.0.0.0/0' -EA SilentlyContinue | "
          r"Sort-Object RouteMetric | Select-Object -First 1).NextHop;"
          r"$dns=(Get-DnsClientServerAddress -AddressFamily IPv4 -EA SilentlyContinue | "
          r"Where-Object ServerAddresses | Select-Object -First 1 -ExpandProperty ServerAddresses);"
          r"[pscustomobject]@{Name=$a.Name;LinkSpeed=$a.LinkSpeed;Gateway=$gw;Dns=($dns -join ',');"
          r"RxErr=$s.ReceivedPacketErrors;TxErr=$s.OutboundPacketErrors;"
          r"RxDisc=$s.ReceivedDiscardedPackets;TxDisc=$s.OutboundDiscardedPackets}"
          r"|ConvertTo-Json -Compress")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return json.loads(out) if out else None
    except Exception:
        return None


# run the probes CONCURRENTLY so worst case is max(dns 19, link 10, ping 5) ~= 19s,
# safely under sysdiag's 25s kill switch even with the resolver fully dead. The gateway ping
# needs the link probe's NextHop first, so it runs after link resolves (still inside the budget).
r = {}
probes = [threading.Thread(target=lambda: r.__setitem__("dns", dns_pair()), daemon=True),
          threading.Thread(target=lambda: r.__setitem__("lk", link()), daemon=True),
          threading.Thread(target=lambda: r.__setitem__("ping", ping()), daemon=True)]
for t in probes:
    t.start()
for t in probes:
    t.join(21)
dns_cold, dns_warm = r.get("dns") or (None, None)
lk = r.get("lk") or {}
gw = lk.get("Gateway")
gw_ms = ping(gw, timeout=2) if gw else None   # localize a fault: gateway up but WAN down = ISP
#                                               problem. 2s cap: this runs after the join, so it
#                                               must stay well under the remaining 25s budget.
print(json.dumps({"net": {"ping_ms": r.get("ping"), "target": "1.1.1.1",
                          "gateway_ms": gw_ms, "gateway": gw, "dns_server": (lk.get("Dns") or None),
                          "dns_ms": dns_warm, "dns_cold_ms": dns_cold,
                          "up": bool(lk.get("Name")), "name": lk.get("Name"),
                          "speed": lk.get("LinkSpeed"),
                          "rx_errors": lk.get("RxErr"), "tx_errors": lk.get("TxErr"),
                          "rx_discards": lk.get("RxDisc"), "tx_discards": lk.get("TxDisc")}}))
```

### `collectors/docker.py`

Container states PARSED to numbers — running/restarting/unhealthy/exited/paused + explicit daemon reachability.

```python
# collectors/docker.py — Docker container state + live resource usage, PARSED to numbers.
# Merges `docker ps` (name/image/status/ports) with `docker stats` (cpu/mem/net/block I/O/pids).
import json, re, subprocess, shutil, os, sys

_DEFAULT = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
DOCKER = shutil.which("docker.exe") or (_DEFAULT if os.path.exists(_DEFAULT) else None)

# go-units: memory uses binary (KiB/MiB/GiB); net & block I/O use decimal (kB/MB/GB).
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
    # raise on a nonzero exit so a DOWN daemon (empty stdout, error on stderr) is distinguishable
    # from a genuinely empty result — otherwise "daemon unreachable" reads as "zero containers".
    r = subprocess.run([DOCKER, *args], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "docker command failed").strip()[:200])
    return [json.loads(line) for line in r.stdout.strip().splitlines() if line.strip()]


def main():
    if not DOCKER:
        print(json.dumps({"docker": {"error": "docker.exe not found (is Docker Desktop installed?)"}}))
        return
    try:
        try:
            ps = _run(["ps", "--all", "--format", "{{json .}}"])
        except Exception as e:
            # daemon down / unreachable — an explicit state, NOT zero containers
            print(json.dumps({"docker": {"daemon_ok": False, "error": str(e)[:200]}}))
            return
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
                "name": r.get("Names"),
                "image": r.get("Image"),
                "status": r.get("Status"),
                "ports": r.get("Ports") or "",
                "cpu_pct": _pct(st.get("CPUPerc")),
                "mem_used_bytes": mem_used,
                "mem_limit_bytes": mem_limit,
                "mem_pct": _pct(st.get("MemPerc")),
                "net_rx_bytes": net_rx,
                "net_tx_bytes": net_tx,
                "blk_read_bytes": blk_r,
                "blk_write_bytes": blk_w,
                "pids": _int(st.get("PIDs")),
            })
        def _status(r):
            return str(r.get("Status", ""))
        running = sum(1 for r in ps if _status(r).startswith("Up"))
        # parse the status string for the states rules.py acts on. Docker writes these verbatim:
        #   "Up 2 hours (unhealthy)", "Restarting (1) 5 seconds ago", "Exited (0) 3 days ago",
        #   "Up 2 hours (Paused)".
        def _exit_code(s):
            m = re.search(r"Exited \((\d+)\)", s)
            return int(m.group(1)) if m else None
        restarting = sum(1 for r in ps if _status(r).startswith("Restarting"))
        unhealthy = sum(1 for r in ps if "(unhealthy)" in _status(r))
        exited = sum(1 for r in ps if _status(r).startswith("Exited"))
        # a container stopped ON PURPOSE shows "Exited (0)" and is NOT a fault; only a NON-ZERO
        # exit (crash) is. Split them so the rule fires on crashes, not intentional stops.
        exited_bad = sum(1 for r in ps if _status(r).startswith("Exited") and (_exit_code(_status(r)) or 0) != 0)
        paused = sum(1 for r in ps if "(Paused)" in _status(r))
        print(json.dumps({"docker": {"daemon_ok": True, "running": running, "total": len(containers),
                                     "restarting": restarting, "unhealthy": unhealthy,
                                     "exited": exited, "exited_bad": exited_bad, "paused": paused,
                                     "containers": containers}}))
    except Exception as e:
        print(json.dumps({"docker": {"error": str(e)}}))


def demo():  # parser self-check: python docker.py --test
    assert _bytes("120MiB") == 125829120
    assert _bytes("1.2kB") == 1200
    assert _bytes("0B") == 0
    assert _pct("0.15%") == 0.15
    assert _pair("120MiB / 7.6GiB") == (125829120, int(7.6 * 1024**3))
    assert _int("12") == 12 and _int(None) is None
    print("docker parsers ok")


if __name__ == "__main__":
    (demo if "--test" in sys.argv else main)()
```

### `collectors/k3s.py`

k3s pods via WSL; judges containerStatuses (catches CrashLoopBackOff that phase='Running' hides) + not-ready.

```python
# collectors/k3s.py — k3s pod state from WSL, via `wsl k3s kubectl`. Degrades if unreachable.
# k3s runs inside WSL, so we shell into WSL to query it. The default runs the bundled kubectl
# as root so it can read /etc/rancher/k3s/k3s.yaml on a stock k3s install.
# ADJUST K3S_CMD if needed:
#   - kubeconfig already set for your WSL user:  ["wsl", "kubectl", "get", "pods", "-A", "-o", "json"]
#   - k3s lives in a non-default distro:          prepend ["wsl", "-d", "Ubuntu", ...]
import json, subprocess

K3S_CMD = ["wsl", "-u", "root", "k3s", "kubectl", "get", "pods", "-A", "-o", "json"]

def main():
    try:
        r = subprocess.run(K3S_CMD, capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            print(json.dumps({"k3s": {"error": (r.stderr or "kubectl failed").strip()[:200]}}))
            return
        items = json.loads(r.stdout).get("items", [])
        pods = []
        crashloop = not_ready = 0
        for i in items:
            st = i.get("status", {}) or {}
            cs = st.get("containerStatuses") or []
            # phase stays 'Running' through a CrashLoopBackOff (k8s semantics), so judge the
            # container states directly, not just the pod phase.
            waiting = [c.get("state", {}).get("waiting", {}).get("reason")
                       for c in cs if isinstance(c, dict)]
            pod_crashloop = any(w == "CrashLoopBackOff" for w in waiting)
            pod_notready = bool(cs) and any(not c.get("ready", False) for c in cs
                                            if isinstance(c, dict)) and st.get("phase") == "Running"
            restarts = sum(int(c.get("restartCount") or 0) for c in cs if isinstance(c, dict))
            crashloop += pod_crashloop
            not_ready += pod_notready and not pod_crashloop
            pods.append({"name": i.get("metadata", {}).get("name"),
                         "namespace": i.get("metadata", {}).get("namespace"),
                         "phase": st.get("phase"), "restarts": restarts,
                         "crashloop": pod_crashloop})
        running = sum(1 for p in pods if p["phase"] == "Running")
        print(json.dumps({"k3s": {"running": running, "total": len(pods),
                                  "crashloop": crashloop, "not_ready": not_ready, "pods": pods}}))
    except Exception as e:
        print(json.dumps({"k3s": {"error": str(e)}}))

if __name__ == "__main__":
    main()
```

### `collectors/whea.py`

Windows hardware-error channel — 7-day-WINDOWED uncorrected count + corrected-machine-check count, Level-based.

```python
# collectors/whea.py — Windows' own hardware-error channel (bad core/DIMM/PCIe/USB ctrl).
# recent_errors is now TIME-WINDOWED (last 7 days) so a single resolved event from years ago
# no longer produces a permanent CRIT — the reported value is CURRENT truth, not "ever, up to 50".
# corrected_7d counts Level-3 corrected machine-checks (the early-warning tier) separately.
# Severity is matched by event Level (1/2 = Critical/Error) not the localized display name, so it
# works on non-English Windows too.
import json, subprocess

# Level: 1=Critical 2=Error 3=Warning. Uncorrected hardware errors log at 1/2; corrected at 3.
ps = (r"$since=(Get-Date).AddDays(-7);"
      r"$e=Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-WHEA-Logger';StartTime=$since} -MaxEvents 200 -ErrorAction SilentlyContinue;"
      r"$e | Select-Object TimeCreated,Id,Level,Message | ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    events = json.loads(out) if out else []
    if isinstance(events, dict):
        events = [events]

    def _msg(e):
        m = e.get("Message")
        return m[:200] if isinstance(m, str) else None

    errs = [e for e in events if e.get("Level") in (1, 2)]
    corrected = [e for e in events if e.get("Level") == 3]
    print(json.dumps({"whea": {"recent_errors": len(errs), "corrected_7d": len(corrected),
                               "window_days": 7,
                               "latest": (_msg(errs[0]) if errs else None)}}))
except Exception as e:
    print(json.dumps({"whea": {"error": str(e)}}))
```

### `collectors/tpm.py`

TPM presence/version via `tpmtool` (works UNELEVATED, unlike Get-Tpm).

```python
# collectors/tpm.py — TPM presence/version via `tpmtool getdeviceinformation`, which returns the
# full truth WITHOUT an elevated shell (unlike Get-Tpm, whose fields come back blank unelevated).
# Falls back to Get-Tpm if tpmtool is unavailable (older Windows). Read-only.
import json, re, subprocess


def _from_tpmtool():
    out = subprocess.run(["tpmtool", "getdeviceinformation"],
                         capture_output=True, text=True, timeout=15).stdout
    if not out.strip():
        return None
    def grab(label):
        m = re.search(rf"{re.escape(label)}\s*:?\s*(.+)", out, re.I)
        return m.group(1).strip() if m else None
    present = grab("TPM Present")
    if present is None:
        return None
    tob = lambda s: None if s is None else s.strip().lower() in ("true", "yes", "1")
    return {"present": tob(present), "version": grab("TPM Version"),
            "manufacturer": grab("TPM Manufacturer ID") or grab("Manufacturer"),
            "ready": tob(grab("Ready For Storage")) if grab("Ready For Storage") else tob(grab("Is Initialized"))}


def _from_gettpm():
    ps = (r"$t=Get-Tpm; [pscustomobject]@{present=$t.TpmPresent;ready=$t.TpmReady;"
          r"enabled=$t.TpmEnabled;owned=$t.TpmOwned}|ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    return d if d.get("present") is not None else None


def main():
    try:
        d = _from_tpmtool()
    except Exception:
        d = None
    if d is None:
        try:
            d = _from_gettpm()
        except Exception:
            d = None
    if d is None:
        print(json.dumps({"tpm": {"error": "TPM detail unavailable (tpmtool + Get-Tpm both blank)"}}))
    else:
        print(json.dumps({"tpm": d}))


if __name__ == "__main__":
    main()
```

### `collectors/me.py`

Intel Management Engine presence/version.

```python
# collectors/me.py — Intel ME / CSME firmware version via the signed driver (no exotic access).
import json, subprocess
ps = (r"$d=Get-CimInstance Win32_PnPSignedDriver|"
      r"Where-Object {$_.DeviceName -match 'Management Engine'}|Select-Object -First 1;"
      r"if($d){[pscustomobject]@{present=$true;version=$d.DriverVersion;name=$d.DeviceName}|"
      r"ConvertTo-Json -Compress}else{'{}'}")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    print(json.dumps({"me": d or {"present": False}}))
except Exception as e:
    print(json.dumps({"me": {"error": str(e)}}))
```

### `collectors/usb.py`

USB device + problem-device counts.

```python
# collectors/usb.py — USB device count + any device in a problem state (xHCI faults via WHEA).
import json, subprocess
ps = (r"$usb=(Get-PnpDevice -Class USB -PresentOnly -EA SilentlyContinue|Measure-Object).Count;"
      r"$bad=(Get-PnpDevice -PresentOnly -EA SilentlyContinue|"
      r"Where-Object {$_.Status -ne 'OK' -and $_.Status -ne 'Unknown'}|Measure-Object).Count;"
      r"[pscustomobject]@{devices=$usb;problems=$bad}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    print(json.dumps({"usb": json.loads(out)}))
except Exception as e:
    print(json.dumps({"usb": {"error": str(e)}}))
```

### `collectors/storage.py`

Physical-drive inventory + SMART health/temp.

```python
# collectors/storage.py — drive health + SMART depth (Get-PhysicalDisk + reliability
# counter: wear/temp/read+write error totals/power-on hours) + disk error events (24h:
# disk/stornvme/storahci — a resetting or timing-out disk logs here before SMART fails).
# Wear/temp/hours are best-effort: many consumer NVMe expose them only elevated -> null.
import json, subprocess
ps = (r"$drives=Get-PhysicalDisk | ForEach-Object {"
      r"$r=$_ | Get-StorageReliabilityCounter -EA SilentlyContinue;"
      r"[pscustomobject]@{name=$_.FriendlyName;media=$_.MediaType;"
      r"health=$_.HealthStatus.ToString();wear=$r.Wear;temp=$r.Temperature;"
      r"read_errs=$r.ReadErrorsTotal;write_errs=$r.WriteErrorsTotal;"
      r"hours=$r.PowerOnHours}};"
      r"$ev=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='disk','stornvme','storahci';Level=1,2,3;"
      r"StartTime=(Get-Date).AddDays(-1)} -EA SilentlyContinue|Measure-Object).Count;"
      r"[pscustomobject]@{drives=@($drives);events=$ev}|ConvertTo-Json -Compress -Depth 4")
try:
    # internal timeout must be SHORTER than sysdiag's 25s kill so our degrade path wins the race
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    d = json.loads(out)
    drives = d["drives"] if isinstance(d["drives"], list) else [d["drives"]]
    drives = [x for x in drives if x]   # PS 5.1 wraps an empty pipeline as [null]
    print(json.dumps({"storage": {"drives": drives, "disk_events_24h": d["events"]}}))
except Exception as e:
    print(json.dumps({"storage": {"error": str(e)}}))
```

### `collectors/os.py`

OS posture: uptime, pending-reboot, CPU microcode (14900K Vmin-shift fix = 0x12B+), BIOS, update age, Secure Boot.

```python
# collectors/os.py — OS posture the other collectors miss: uptime, pending-reboot, CPU microcode
# (the 14900K Vmin-shift fix is 0x12B+), BIOS version, days since last update, NTP clock offset,
# host Secure Boot. All read-only; each field independently guarded so one failure can't blank
# the rest. Windows-only; a non-Windows host reports present:false.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
try { $b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime
      $out.uptime_days = [math]::Round(((Get-Date)-$b).TotalDays,2) } catch {}
try {
  $pending = $false
  if (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') { $pending=$true }
  if (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') { $pending=$true }
  $pfro = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' -Name PendingFileRenameOperations -EA SilentlyContinue)
  if ($pfro.PendingFileRenameOperations) { $pending=$true }
  $out.pending_reboot = [bool]$pending
} catch {}
try { $r=(Get-ItemProperty 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -EA Stop)
      $mc = $r.'Update Revision'
      if ($mc -ne $null) { $out.microcode = ('0x{0:X}' -f [int64]([BitConverter]::ToUInt64(($mc+ ,0*8)[0..7],0))) } } catch {}
try { $bios=Get-CimInstance Win32_BIOS -EA Stop
      $out.bios_version = ($bios.SMBIOSBIOSVersion) } catch {}
try { $hf=Get-CimInstance Win32_QuickFixEngineering -EA Stop | Where-Object InstalledOn | Sort-Object InstalledOn | Select-Object -Last 1
      if ($hf.InstalledOn) { $out.win_update_age_days = [int]((Get-Date)-$hf.InstalledOn).TotalDays } } catch {}
try { $s=w32tm /query /status 2>$null | Select-String 'Phase Offset'
      if ($s) { $v=($s -replace '.*:\s*','' -replace 's$','').Trim()
                $out.ntp_offset_ms = [math]::Round([double]$v*1000,1) } } catch {}
# Secure Boot via the registry (no elevation, unlike Confirm-SecureBootUEFI)
try { $sb=(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' -Name UEFISecureBootEnabled -EA Stop)
      $out.secure_boot = [bool]$sb.UEFISecureBootEnabled } catch {}
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"os": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        print(json.dumps({"os": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"os": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
```

### `collectors/security.py`

Defender real-time protection + signature age, firewall, VBS/HVCI, BitLocker, failed-logon count.

```python
# collectors/security.py — security posture: Defender real-time protection + signature age,
# firewall, BitLocker on C:, VBS/HVCI, failed-logon count (24h). Read-only; each field guarded.
# Windows-only. Some fields (BitLocker, failed logons) read fuller when elevated but degrade
# to a clean absence rather than a falsehood when they can't be read.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
try { $m=Get-MpComputerStatus -EA Stop
      $out.defender_on = [bool]$m.RealTimeProtectionEnabled
      if ($m.AntivirusSignatureLastUpdated) {
        $out.defender_sig_age_days = [int]((Get-Date)-$m.AntivirusSignatureLastUpdated).TotalDays } } catch {}
try { $fw=Get-NetFirewallProfile -EA Stop
      $out.firewall_on = [bool](($fw | Where-Object Enabled -eq $true | Measure-Object).Count -gt 0) } catch {}
try { $bl=Get-BitLockerVolume -MountPoint 'C:' -EA Stop
      $out.bitlocker_c = [string]$bl.ProtectionStatus } catch {}
try { $dg=Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard -EA Stop
      $out.vbs_on = [bool]($dg.VirtualizationBasedSecurityStatus -eq 2) } catch {}
try { $t=(Get-Date).AddDays(-1)
      $n=(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625;StartTime=$t} -EA Stop | Measure-Object).Count
      $out.failed_logons_24h = [int]$n } catch {}
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"security": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        print(json.dumps({"security": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"security": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
```

### `collectors/events.py`

Event-log health: WDDM TDR GPU resets (4101), app crashes (1000), NTFS corruption (55), failed scheduled tasks.

```python
# collectors/events.py — Windows event-log health signals no other collector covers:
# GPU driver resets (WDDM TDR, Event 4101 — the canonical GPU-instability signal), application
# crashes (WER 1001 / Application Error 1000), NTFS corruption (Event 55), and scheduled tasks
# whose last run failed (history.py itself runs from Task Scheduler — its silent failure is
# otherwise invisible). All time-windowed; read-only. Windows-only.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
$since = (Get-Date).AddDays(-7)
$since1 = (Get-Date).AddDays(-1)
try { $out.gpu_tdr_7d = [int]((Get-WinEvent -FilterHashtable @{LogName='System';Id=4101;StartTime=$since} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.gpu_tdr_7d = 0 }
try { $out.app_crashes_24h = [int]((Get-WinEvent -FilterHashtable @{LogName='Application';ProviderName='Application Error';Id=1000;StartTime=$since1} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.app_crashes_24h = 0 }
try { $out.ntfs_errors_24h = [int]((Get-WinEvent -FilterHashtable @{LogName='System';Id=55;StartTime=$since1} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.ntfs_errors_24h = 0 }
try {
  # Windows' OWN maintenance tasks (\Microsoft\*) routinely report non-zero results benignly, and
  # several result codes mean "running / not-yet-run / disabled / terminated-by-user" not "failed".
  # Exclude both so this surfaces a task the OPERATOR set up that is genuinely failing, not OS noise.
  $benign = @(0, 1, 267009, 267010, 267011, 267012, 267014)
  $f = Get-ScheduledTask -EA Stop |
       Where-Object { $_.TaskPath -notlike '\Microsoft\*' } |
       ForEach-Object { $ti = $_ | Get-ScheduledTaskInfo -EA SilentlyContinue
         if ($ti -and ($benign -notcontains $ti.LastTaskResult) -and $ti.LastRunTime -gt $since) { $_.TaskName } } |
       Select-Object -First 10
  $out.task_failures = @($f) } catch { $out.task_failures = @() }
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"events": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        if isinstance(data, dict):
            tf = data.get("task_failures")
            if tf is None:
                data["task_failures"] = []
            elif not isinstance(tf, list):
                data["task_failures"] = [tf]        # PS emits a bare string for a single item
        print(json.dumps({"events": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"events": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
```

### `collectors/procs.py`

Top CPU / RAM / per-process GPU-VRAM consumers (names the chat model's own footprint).

```python
# collectors/procs.py — top resource consumers, so "my machine is slow / hot / full" gets a
# named culprit. top_cpu (rough %, one 250ms sample), top_mem (working set MB), and top_gpu_vram
# (per-process VRAM via nvidia-smi — this is what names ollama.exe as the reason gpu.vram_pct is
# high, answering the chat brain's observer effect). Read-only. Windows-primary; nvidia part
# is cross-platform where nvidia-smi exists.
import json, platform, shutil, subprocess

PS = r"""
$out = [ordered]@{}
try {
  $n = [math]::Max(1,(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors)
  # two TotalProcessorTime snapshots 300ms apart -> real instantaneous CPU% per process,
  # normalized by logical-core count (Win32_PerfFormattedData_PerfProc_Process is empty on
  # some boxes; this Get-Process delta method is reliable everywhere).
  $a = @{}; Get-Process -EA SilentlyContinue | ForEach-Object { $a[$_.Id] = @($_.ProcessName, $_.TotalProcessorTime.TotalMilliseconds) }
  Start-Sleep -Milliseconds 300
  $rows = Get-Process -EA SilentlyContinue | ForEach-Object {
    if ($a.ContainsKey($_.Id)) {
      $d = $_.TotalProcessorTime.TotalMilliseconds - $a[$_.Id][1]
      [pscustomobject]@{ name=$a[$_.Id][0]; cpu_pct=[math]::Round(100*$d/300/$n,1) }
    }
  } | Where-Object { $_.name -ne 'Idle' -and $_.cpu_pct -gt 0 }
  $out.top_cpu = @($rows | Sort-Object cpu_pct -Descending | Select-Object -First 5 |
    ForEach-Object { [ordered]@{ name=$_.name; cpu_pct=$_.cpu_pct } })
} catch {}
try {
  $out.top_mem = @(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 |
    ForEach-Object { [ordered]@{ name=$_.ProcessName; mem_mb=[int]($_.WorkingSet64/1MB) } })
} catch {}
[pscustomobject]$out | ConvertTo-Json -Depth 4 -Compress
"""


def _gpu_vram():
    smi = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
    try:
        r = subprocess.run([smi, "--query-compute-apps=process_name,used_memory",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=6)
        procs = []
        for line in r.stdout.strip().splitlines():
            if "," in line:
                name, mem = line.rsplit(",", 1)
                try:
                    procs.append({"name": name.strip(), "vram_mb": int(float(mem))})
                except ValueError:
                    continue
        return sorted(procs, key=lambda p: -p["vram_mb"])[:5]
    except Exception:
        return None


def main():
    data = {}
    if platform.system() == "Windows":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                                 capture_output=True, text=True, timeout=20).stdout.strip()
            d = json.loads(out) if out else {}
            if isinstance(d, dict):
                data.update(d)
        except Exception as e:
            data["error"] = str(e)[:150]
    tg = _gpu_vram()
    if tg is not None:
        data["top_gpu_vram"] = tg
    print(json.dumps({"procs": data}))


if __name__ == "__main__":
    main()
```

### `collectors/wsl.py`

The WSL2 utility VM Docker/k3s run inside — vmmem working set + ext4 vhdx size (both otherwise invisible).

```python
# collectors/wsl.py — the WSL2 utility VM this box's Docker + k3s actually run inside, which
# every other collector is blind to: vmmem working set (RAM the VM holds) and the ext4 .vhdx
# size (grows unbounded, never auto-shrinks). Read-only. Windows-only (WSL is a Windows feature).
import json, os, platform, subprocess, glob


def _vmmem_gb():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-Process 'vmmem','vmmemWSL' -EA SilentlyContinue | "
                              "Measure-Object WorkingSet64 -Sum).Sum"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return round(int(out) / 1024**3, 2) if out and out.isdigit() else None
    except Exception:
        return None


def _vhdx_gb():
    # Sum every WSL distro's *.vhdx. Store distros live under %LOCALAPPDATA%\Packages\*\LocalState;
    # others (incl. Docker Desktop's) register a BasePath under HKCU\...\Lxss\{guid}. Read both.
    paths = set()
    base = os.path.expandvars(r"%LOCALAPPDATA%\Packages")
    for p in glob.glob(os.path.join(base, "*", "LocalState", "*.vhdx")):
        paths.add(p)
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Lxss")
        for i in range(winreg.QueryInfoKey(key)[0]):
            sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
            try:
                bp = winreg.QueryValueEx(sub, "BasePath")[0]
                bp = os.path.expandvars(bp.replace("\\\\?\\", ""))
                for p in glob.glob(os.path.join(bp, "*.vhdx")):
                    paths.add(p)
            except OSError:
                pass
            finally:
                winreg.CloseKey(sub)
        winreg.CloseKey(key)
    except Exception:
        pass
    total, found = 0, False
    for p in paths:
        try:
            total += os.path.getsize(p)
            found = True
        except OSError:
            continue
    return round(total / 1024**3, 2) if found else None


def main():
    if platform.system() != "Windows":
        print(json.dumps({"wsl": {"present": False, "note": "windows-only collector"}}))
        return
    data = {}
    v = _vmmem_gb()
    d = _vhdx_gb()
    if v is not None:
        data["vmmem_gb"] = v
    if d is not None:
        data["vhdx_gb"] = d
    if not data:
        data = {"present": False, "note": "no running WSL VM / vhdx found"}
    print(json.dumps({"wsl": data}))


if __name__ == "__main__":
    main()
```

### `collectors/power.py`

Boot/power forensics from the event log (Kernel-Power 41 / 6008 / throttle 37).

```python
# collectors/power.py — power/boot forensics from the System event log: Kernel-Power 41
# (machine died without a clean shutdown: PSU trip, hard hang, thermal cutoff), EventLog
# 6008 (unexpected shutdown), Kernel-Processor-Power 37 (firmware throttled the CPU).
# This is the software-visible shadow of the motherboard's debug LEDs.
import json, subprocess
ps = (r"$d7=(Get-Date).AddDays(-7);$d1=(Get-Date).AddDays(-1);"
      r"$dirty=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-Kernel-Power';Id=41;StartTime=$d7}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"$unex=(Get-WinEvent -FilterHashtable @{LogName='System';Id=6008;StartTime=$d7}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"$thr=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-Kernel-Processor-Power';Id=37;StartTime=$d1}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"[pscustomobject]@{dirty=$dirty;unexpected=$unex;throttle=$thr}|ConvertTo-Json -Compress")
try:
    # internal timeout must be SHORTER than sysdiag's 25s kill so our degrade path wins the race
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"power": {"dirty_reboots_7d": d["dirty"],
                                "unexpected_shutdowns_7d": d["unexpected"],
                                "cpu_throttle_events_24h": d["throttle"]}}))
except Exception as e:
    print(json.dumps({"power": {"error": str(e)}}))
```

### `collectors/lights.py`

Board/RGB zone state via the OpenRGB SDK server (127.0.0.1:6742).

```python
# collectors/lights.py — board/RGB light state via the OpenRGB SDK server (127.0.0.1:6742).
# Reads every registered RGB device (motherboard, GPU, DRAM, strips) and how many LEDs are
# actually lit. HONEST LIMIT: POST/EZ-Debug LEDs (CPU/DRAM/VGA/BOOT) are hardware-driven
# during boot and NOT software-readable — for that failure class see power.py (dirty
# reboots) and whea.py. RGB state IS still diagnostic: a dead zone = dead header/device.
# Degrades to a note (not an error) — dark RGB is not a health warning.
import json
try:
    from openrgb import OpenRGBClient
    c = OpenRGBClient(address="127.0.0.1", port=6742, name="sysdiag")
    devs = []
    for d in c.devices:
        lit = sum(1 for led in d.colors if led.red or led.green or led.blue)
        devs.append({"name": d.name, "type": d.type.name, "leds": len(d.colors), "lit": lit})
    c.disconnect()
    print(json.dumps({"lights": {"devices": devs}}))
except ImportError:
    print(json.dumps({"lights": {"note": "openrgb-python not installed (optional)"}}))
except Exception as e:
    print(json.dumps({"lights": {"note": f"OpenRGB SDK not reachable: {e}"}}))
```

### `collectors/vm.py`

Hyper-V VMs + their encryption posture (encrypted state, vTPM, Secure Boot, Shielded).

```python
# collectors/vm.py — virtual machines and their ENCRYPTION posture. Windows/Hyper-V:
# per-VM state + whether the VM's state/migration traffic is encrypted, whether it has a
# virtual TPM, and Secure Boot (the pieces of a Hyper-V "shielded"/encrypted VM). Reports
# counts + a running-VM count for the graph. Degrades to present:false when Hyper-V is absent.
#
# NOTE: needs an ELEVATED shell for full Get-VMSecurity detail on some hosts; unelevated it
# still lists VMs and state. Linux/libvirt hosts run a different collector (see the Linux note
# in README); this is the Windows Hyper-V collector.
import json, subprocess

# Get-VM may be missing entirely (Hyper-V role not installed) -> the whole block throws and
# we degrade. Per VM we pull state + the three encryption-relevant security flags.
ps = (
    r"if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) { '[]'; exit }"
    r"$vms = Get-VM | ForEach-Object {"
    r"  $s = $null; try { $s = Get-VMSecurity -VMName $_.Name -ErrorAction SilentlyContinue } catch {}"
    r"  $fw = $null; try { $fw = Get-VMFirmware -VMName $_.Name -ErrorAction SilentlyContinue } catch {}"
    r"  [pscustomobject]@{"
    r"    name = $_.Name; state = $_.State.ToString();"
    r"    encrypted = [bool]$s.EncryptStateAndVmMigrationTraffic;"
    r"    vtpm = [bool]$s.TpmEnabled;"
    r"    shielded = [bool]$s.Shielded;"
    r"    secure_boot = ($fw.SecureBoot -eq 'On')"
    r"  }"
    r"}; @($vms) | ConvertTo-Json -Compress -Depth 4"
)
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    vms = json.loads(out) if out and out != "[]" else []
    if isinstance(vms, dict):
        vms = [vms]
    if not vms:
        print(json.dumps({"vm": {"present": False}}))   # Hyper-V absent or no VMs defined
    else:
        running = sum(1 for v in vms if v.get("state") == "Running")
        encrypted = sum(1 for v in vms if v.get("encrypted"))
        print(json.dumps({"vm": {"present": True, "total": len(vms), "running": running,
                                 "encrypted": encrypted, "vms": vms}}))
except Exception as e:
    print(json.dumps({"vm": {"error": str(e)}}))
```

### `collectors/services.py`

systemd units via `wsl systemctl` (bridges into WSL like k3s.py); running + failed.

```python
# collectors/services.py — Linux systemd service state (the `systemctl start xxx` units).
# Reports running-service count + any FAILED units by name. Runs natively on a Linux host
# (the Linux release) and, on a Windows host, bridges into WSL — exactly like k3s.py — so a
# Windows box can still watch the systemd services inside its WSL distro. Degrades cleanly
# when systemd is reachable nowhere (WSL1, no distro, systemd disabled).
#
# Two Windows gotchas this handles: (1) systemctl output is UTF-8 (the '●' status glyph is
# 0xE2 0x97 0x8F) — we decode utf-8/replace, not the cp1252 locale codec, or a failed unit's
# bullet crashes the decode. (2) `systemctl list-units` prints a leading '●' column for
# troubled units — `--plain` drops it so we parse the real unit name.
import json, os, shutil, subprocess

# a real systemd `is-system-running` answer is one of these; anything else (command-not-found,
# wsl's UTF-16 "no distribution" banner, empty) means systemd isn't actually reachable here
VALID = {"running", "degraded", "maintenance", "starting", "stopping", "initializing"}


def systemctl_base():
    if os.name == "posix" and shutil.which("systemctl"):
        return ["systemctl"]                        # native Linux with systemd
    # Windows (or no native systemd): try WSL, where modern WSL2 runs systemd if enabled.
    # ADJUST like k3s.py if your distro isn't the default: prepend ["wsl","-d","Ubuntu",...]
    if shutil.which("wsl"):
        return ["wsl", "systemctl"]
    return None


def run(base, *args):
    r = subprocess.run(base + list(args) + ["--plain", "--no-pager", "--no-legend"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=20)
    return r.stdout or ""


base = systemctl_base()
try:
    if not base:
        print(json.dumps({"services": {"present": False}}))   # no systemd anywhere reachable
        raise SystemExit
    probe = subprocess.run(base + ["is-system-running"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
    status = (probe.stdout or "").strip()
    if status not in VALID:            # command-not-found / no-distro / WSL1 / systemd disabled
        print(json.dumps({"services": {"present": False, "note": f"systemd not reachable ({status or 'no answer'})"}}))
        raise SystemExit
    running = [ln.split()[0] for ln in run(base, "list-units", "--type=service",
                                           "--state=running").splitlines() if ln.strip()]
    failed = [ln.split()[0] for ln in run(base, "list-units", "--type=service",
                                          "--state=failed").splitlines() if ln.strip()]
    print(json.dumps({"services": {"present": True, "running": len(running),
                                   "failed": len(failed), "failed_units": failed,
                                   "state": status}}))
except SystemExit:
    raise
except Exception as e:
    print(json.dumps({"services": {"error": str(e)}}))
```

### `collectors/ssh.py`

Scrape remote Linux VMs over SSH — read-only checks with thresholds. See INSTRUCTIONS §8.

```python
# collectors/ssh.py — scrape components living on remote Linux VMs by SSHing in and running
# read-only checks (a "check" is a shell command; reading a file is just `cat`/`grep /path`).
# Shells out to the OpenSSH client (ships with Win10/11 + every Linux) exactly like k3s.py
# shells to `wsl` — no pip deps. Configure targets in ssh.config.json (see the example);
# absent config -> present:false, so this collector is a no-op until you set it up.
#
# SECURITY (this is a network + auth surface — the defaults are the safe ones):
#   * KEY-BASED AUTH ONLY. BatchMode=yes disables password prompts (no hangs, no passwords in
#     a config file). Set up an SSH key to each VM first (ssh-copy-id / authorized_keys).
#   * HOST KEYS ARE CHECKED. StrictHostKeyChecking stays on; a new VM must be in known_hosts,
#     or set "accept_new": true per target for trust-on-first-use (accept-new, never "no").
#   * Point checks at READ-ONLY commands. The collector only reads; what your commands do is
#     yours to keep read-only.
#   * One SSH session per target (all its checks run in that one session); targets run in
#     parallel with per-connect timeouts so an unreachable VM degrades instead of hanging.
import json, math, os, re, shlex, shutil, subprocess, threading, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.environ.get("WATCHTOWER_SSH_CONFIG", os.path.join(REPO, "ssh.config.json"))
SSH = shutil.which("ssh")
# user@host / host; first char alnum/./_ so a value can't start with '-' and pose as an ssh
# option (e.g. -oProxyCommand=...). Belt-and-suspenders — the config is operator-authored.
DEST_RE = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._-]*(@[A-Za-z0-9._][A-Za-z0-9._-]*)?$")
BUDGET = 20          # wall-clock ceiling for the whole collector, under the 25s parent kill
PER_TARGET = 14      # per-target ssh cap; < BUDGET so one target can't blow the whole budget


def _coerce(s):
    s = s.strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        f = float(s)
        return f if math.isfinite(f) else s   # keep nan/inf as text -> valid JSON, no fake pass
    except ValueError:
        return s


def _normalize_checks(raw):
    """Each check -> {'cmd': str, 'warn'?, 'crit'?, 'unit'?}. Accepts a bare command string
    or an object with thresholds. Names carrying a tab/newline are dropped — they'd corrupt
    the name<TAB>value wire format."""
    out = {}
    for name, spec in (raw or {}).items():
        name = str(name)
        if "\t" in name or "\n" in name:
            continue
        if isinstance(spec, str):
            out[name] = {"cmd": spec}
        elif isinstance(spec, dict) and isinstance(spec.get("cmd"), str):
            out[name] = {k: spec[k] for k in ("cmd", "warn", "crit", "unit") if k in spec}
    return out


def _remote_script(checks):
    # run every check in ONE ssh session; emit "name<TAB>value" per line, each value capped
    lines = []
    for name, spec in checks.items():
        n = shlex.quote(name)
        # { cmd ; } isolates the operator's command; head -c caps output; tr flattens newlines
        lines.append(f"printf %s {n}; printf '\\t'; {{ {spec['cmd']} ; }} 2>/dev/null "
                     f"| head -c 500 | tr '\\n' ' '; printf '\\n'")
    return " ; ".join(lines)


def _scrape(target, connect_timeout):
    name = str(target.get("name") or target.get("ssh") or "?")
    # EVERYTHING that can raise on operator-typo'd config lives inside this try, so one bad
    # target degrades to reachable:false instead of taking down the whole collector.
    try:
        dest = target.get("ssh") or target.get("host")
        checks = _normalize_checks(target.get("checks"))
        if not dest or not DEST_RE.match(str(dest)):
            return name, {"reachable": False, "error": "invalid or missing 'ssh' destination"}
        if not checks:
            return name, {"reachable": False, "error": "no checks configured"}
        port = int(target.get("port") or 22)        # '' / None / '22a' -> caught below
        strict = "accept-new" if target.get("accept_new") else "yes"
        argv = [SSH, "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no",
                "-o", f"ConnectTimeout={connect_timeout}",
                "-o", f"StrictHostKeyChecking={strict}", "-p", str(port)]
        key = target.get("key")
        if key:
            argv += ["-o", "IdentitiesOnly=yes", "-i", os.path.expanduser(str(key))]
        jump = target.get("jump")                   # optional bastion/ProxyJump
        if jump and DEST_RE.match(str(jump)):
            argv += ["-J", str(jump)]
        argv += [str(dest), _remote_script(checks)]
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=PER_TARGET)
    except subprocess.TimeoutExpired:
        return name, {"reachable": False, "error": "timeout"}
    except Exception as e:
        return name, {"reachable": False, "error": str(e)[:150]}
    if r.returncode != 0:
        return name, {"reachable": False, "error": (r.stderr or "ssh failed").strip()[:150]}

    got = {}
    for line in r.stdout.splitlines():
        if "\t" not in line:
            continue
        cname, raw = line.split("\t", 1)
        spec = checks.get(cname, {})
        entry = {"value": _coerce(raw)}
        for k in ("warn", "crit", "unit"):
            if k in spec:
                entry[k] = spec[k]
        got[cname] = entry
    return name, {"reachable": True, "checks": got}


def main():
    if not SSH:
        print(json.dumps({"ssh": {"present": False, "note": "no ssh client on PATH"}}))
        return
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(json.dumps({"ssh": {"present": False}}))          # unconfigured = no-op
        return
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"ssh": {"error": f"ssh.config.json: {e}"}}))
        return

    targets = cfg.get("targets") if isinstance(cfg, dict) else None
    if not isinstance(targets, list) or not targets:
        print(json.dumps({"ssh": {"present": False}}))
        return
    try:
        ct = max(1, min(int(cfg.get("connect_timeout", 6)), 8))
    except (TypeError, ValueError):
        ct = 6

    # daemon workers + a hard wall-clock join deadline: the collector ALWAYS returns within
    # BUDGET (< the 25s parent kill), even with a hung post-auth check or a large fleet.
    # Targets not finished by the deadline are reported as budget-exceeded rather than losing
    # the whole ssh namespace (which is what a parent-timeout kill would do).
    results, lock, sem = {}, threading.Lock(), threading.Semaphore(24)

    def work(t):
        with sem:
            name, r = _scrape(t, ct)
        with lock:
            results[name] = r

    threads = [threading.Thread(target=work, args=(t,), daemon=True) for t in targets]
    deadline = time.monotonic() + BUDGET
    for th in threads:
        th.start()
    for th in threads:
        th.join(max(0.0, deadline - time.monotonic()))
    for t in targets:                               # fill in anything the deadline cut off
        name = str(t.get("name") or t.get("ssh") or "?")
        with lock:
            results.setdefault(name, {"reachable": False, "error": "collector time budget exceeded"})
    down = sum(1 for r in results.values() if not r.get("reachable"))
    print(json.dumps({"ssh": {"present": True, "down": down, "targets": results}}))


if __name__ == "__main__":
    main()
```

### SDR / antenna skeletons

These run today (emit `present:false`) and carry `FILL-ME` blocks to complete when the radio arrives. `_sdr_common.py` is shared (underscore = library).

### `collectors/_sdr_common.py`

Shared SDR probe (underscore = library, snapshot() skips it).

```python
# collectors/_sdr_common.py — shared SDR probe. Underscore prefix = snapshot() skips it
# (it's a library, not a collector). Used by sdr.py / rx.py / tx.py / tuner.py.
import json, re, subprocess

# USB signatures of common SDRs; PID None = any product from that vendor.
KNOWN = {
    ("0BDA", "2832"): "RTL-SDR (RTL2832U)",
    ("0BDA", "2838"): "RTL-SDR (RTL2832U)",
    ("1D50", "6089"): "HackRF One",
    ("1D50", "60A1"): "Airspy",
    ("1D50", "6108"): "LimeSDR",
    ("0456", "B673"): "ADALM-Pluto",
    ("2500", None):   "Ettus USRP",
    ("1DF7", None):   "SDRplay RSP",
}


def usb_sdrs():
    """SDRs visible on USB right now (no SDR libraries needed) -> [labels]."""
    ps = r"Get-PnpDevice -PresentOnly -EA SilentlyContinue | Select-Object -ExpandProperty InstanceId"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    found = []
    for vid, pid in set(re.findall(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", out, re.I)):
        label = KNOWN.get((vid.upper(), pid.upper())) or KNOWN.get((vid.upper(), None))
        if label and label not in found:
            found.append(label)
    return found


def soapy_devices():
    """Enumerate via SoapySDR if installed -> [ {driver, label, serial, ...} ] or None."""
    try:
        import SoapySDR
    except ImportError:
        return None
    return [dict(kw) for kw in SoapySDR.Device.enumerate()]


def absent(namespace):
    """The degrade contract: hardware not present is a STATE, not an error finding."""
    print(json.dumps({namespace: {"present": False}}))
```

### `collectors/sdr.py`

```python
# collectors/sdr.py — SDR device inventory. SKELETON: runs today (emits present:false
# with no hardware); fill the FILL-ME blocks when the SDR arrives.
# Detection is two-layer: USB VID:PID (works with zero SDR software) then SoapySDR
# enumeration (works for anything with a Soapy driver: rtl-sdr, HackRF, Lime, USRP...).
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

usb = usb_sdrs()
soapy = soapy_devices()          # None = SoapySDR not installed; [] = installed, none found

if not usb and not soapy:
    absent("sdr")
    raise SystemExit

devices = []
for kw in (soapy or []):
    dev = {"driver": kw.get("driver"), "label": kw.get("label"), "serial": kw.get("serial"),
           "rx_channels": None, "tx_channels": None}
    # FILL-ME(channel counts): opening the device is device-specific and can be slow —
    # uncomment once you know your hardware behaves:
    #   import SoapySDR
    #   sd = SoapySDR.Device(kw)
    #   dev["rx_channels"] = sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)
    #   dev["tx_channels"] = sd.getNumChannels(SoapySDR.SOAPY_SDR_TX)
    #   dev["clock_source"] = sd.getClockSource()
    devices.append(dev)

print(json.dumps({"sdr": {
    "present": True,
    "usb": usb,                          # what the bus sees, even with no drivers installed
    "soapy_installed": soapy is not None,
    "devices": devices,
}}))
```

### `collectors/rx.py`

```python
# collectors/rx.py — receive-channel state. SKELETON: emits present:false until the SDR
# arrives and the FILL-ME block is completed for your hardware.
#
# The intended shape per channel — this is what rules.py will threshold on:
#   {"id": 0, "kind": "wideband"|"narrowband", "freq_hz": ..., "rate_hz": ..., "gain_db": ...,
#    "power_dbfs": ..., "noise_floor_dbfs": ..., "active": bool}
#
# "Is the channel on?" = measured channel power sits above the noise floor by a margin:
#   active = power_dbfs > noise_floor_dbfs + MARGIN_DB
# Calibrate MARGIN_DB (start ~6 dB) and the floor against YOUR antenna/environment —
# the floor is not a constant, sample it with the antenna terminated or at a quiet freq.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

MARGIN_DB = 6.0   # ponytail: fixed margin; make it per-channel if bands differ a lot

if not usb_sdrs() and not soapy_devices():
    absent("rx")
    raise SystemExit


def measure_channel(sd, ch):
    """FILL-ME: read a short burst and compute power. Reference implementation:

    import SoapySDR, numpy as np
    st = sd.setupStream(SoapySDR.SOAPY_SDR_RX, "CF32", [ch])
    sd.activateStream(st)
    buf = np.empty(8192, np.complex64)
    sr = sd.readStream(st, [buf], len(buf), timeoutUs=int(2e5))
    sd.deactivateStream(st); sd.closeStream(st)
    if sr.ret <= 0:
        return None
    power = 10 * np.log10(np.mean(np.abs(buf[:sr.ret]) ** 2) + 1e-20)
    return {
        "id": ch,
        "kind": "wideband" if sd.getSampleRate(SoapySDR.SOAPY_SDR_RX, ch) > 2e6 else "narrowband",
        "freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_RX, ch),
        "rate_hz": sd.getSampleRate(SoapySDR.SOAPY_SDR_RX, ch),
        "gain_db": sd.getGain(SoapySDR.SOAPY_SDR_RX, ch),
        "power_dbfs": round(power, 1),
        "noise_floor_dbfs": NOISE_FLOOR,          # FILL-ME: calibrate, don't hardcode
        "active": power > NOISE_FLOOR + MARGIN_DB,
    }
    """
    return None


channels = []
# FILL-ME: open each device and measure each Rx channel:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           m = measure_channel(sd, ch)
#           if m: channels.append(m)

print(json.dumps({"rx": {"present": True, "channels": channels,
                         "note": "skeleton — fill measure_channel() for your SDR"}}))
```

### `collectors/tx.py`

```python
# collectors/tx.py — transmit-chain state. SKELETON: emits present:false until filled.
#
# Target shape per channel:
#   {"id": 0, "enabled": bool, "freq_hz": ..., "rate_hz": ..., "gain_db": ...}
#
# HONEST LIMIT: most SDRs cannot self-report actual RF power leaving the antenna port —
# "enabled + configured" is what the API gives you. If you need proof of emission, the
# two real options are (a) a directional coupler feeding one of your OWN Rx channels
# (then rx.py's power-above-floor check IS your Tx confirmation), or (b) a hardware
# power meter. Wire whichever you pick into verify_emission() below.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

if not usb_sdrs() and not soapy_devices():
    absent("tx")
    raise SystemExit


def verify_emission(ch):
    """FILL-ME (optional): loopback/coupler check that Tx RF is actually present."""
    return None


channels = []
# FILL-ME: enumerate Tx channels and their configured state:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_TX)):
#           channels.append({
#               "id": ch,
#               "freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_TX, ch),
#               "rate_hz": sd.getSampleRate(SoapySDR.SOAPY_SDR_TX, ch),
#               "gain_db": sd.getGain(SoapySDR.SOAPY_SDR_TX, ch),
#               "enabled": None,        # device-specific: stream active / PA enabled
#               "emission_verified": verify_emission(ch),
#           })

print(json.dumps({"tx": {"present": True, "channels": channels,
                         "note": "skeleton — fill Tx enumeration for your SDR"}}))
```

### `collectors/tuner.py`

```python
# collectors/tuner.py — tuner/frontend state. SKELETON: emits present:false until filled.
#
# Target shape per tuner:
#   {"id": 0, "type": "R820T2"|..., "locked": bool, "ppm": ..., "agc": bool,
#    "lo_freq_hz": ..., "bandwidth_hz": ...}
#
# "locked" = the PLL achieved lock at the requested LO frequency — the tuner-level
# equivalent of "is this input on". Most drivers surface it as a failed setFrequency /
# a status flag; rtl-sdr exposes tuner type + PPM directly (librtlsdr get_tuner_type).
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

if not usb_sdrs() and not soapy_devices():
    absent("tuner")
    raise SystemExit

tuners = []
# FILL-ME: per-driver frontend introspection. Soapy generic version:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           tuners.append({
#               "id": ch,
#               "type": kw.get("tuner") or kw.get("driver"),
#               "lo_freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_RX, ch, "RF"),
#               "bandwidth_hz": sd.getBandwidth(SoapySDR.SOAPY_SDR_RX, ch),
#               "agc": bool(sd.getGainMode(SoapySDR.SOAPY_SDR_RX, ch)),
#               "ppm": sd.getFrequencyCorrection(SoapySDR.SOAPY_SDR_RX, ch),
#               "locked": None,   # FILL-ME: driver-specific lock/status sensor, e.g.
#                                 # "lo_locked" in sd.listSensors(SOAPY_SDR_RX, ch)
#           })

print(json.dumps({"tuner": {"present": True, "tuners": tuners,
                            "note": "skeleton — fill frontend introspection for your SDR"}}))
```

### `collectors/antenna.py`

```python
# collectors/antenna.py — antenna/front-end state per SDR Rx channel. SKELETON: runs today
# (emits present:false with no SDR), fill the FILL-ME block when the radio + antennas arrive.
#
# Distinct from sdr.py (device inventory) and rx.py (channel power): this reports, per
# channel, WHICH antenna port is selected, the choices available, and — where the hardware
# exposes it — received signal strength (RSSI) and standing-wave ratio (SWR).
#
# HONEST LIMIT on SWR: most receive-only SDRs (RTL-SDR, Airspy, plain HackRF Rx) have NO way
# to measure SWR — that needs a directional/return-loss bridge on a TX-capable chain (some
# USRP/Lime setups, or an external VNA/SWR meter). So swr stays null unless your hardware and
# the FILL-ME wiring actually provide it; RSSI is available on more devices via a Soapy sensor.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

if not usb_sdrs() and not soapy_devices():
    absent("antenna")
    raise SystemExit

antennas = []
# FILL-ME: enumerate the antenna port per Rx channel + optional RSSI/SWR sensors.
# Soapy generic version:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           sensors = sd.listSensors(SoapySDR.SOAPY_SDR_RX, ch)
#           rssi = float(sd.readSensor(SoapySDR.SOAPY_SDR_RX, ch, "RSSI")) if "RSSI" in sensors else None
#           swr = float(sd.readSensor(SoapySDR.SOAPY_SDR_RX, ch, "SWR")) if "SWR" in sensors else None
#           antennas.append({
#               "id": ch,
#               "selected": sd.getAntenna(SoapySDR.SOAPY_SDR_RX, ch),   # e.g. "RX2" / "TX/RX"
#               "options": list(sd.listAntennas(SoapySDR.SOAPY_SDR_RX, ch)),
#               "rssi_dbm": rssi,
#               "swr": swr,                 # null on receive-only radios (no return-loss bridge)
#           })

print(json.dumps({"antenna": {"present": True, "antennas": antennas,
                              "note": "skeleton — fill port/RSSI/SWR introspection for your SDR"}}))
```

## 5. Truth-layer aggregator, live sampler, chat brain & UI

### `sysdiag.py`

```python
import json, glob, subprocess, sys, pathlib, argparse
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).parent


def snapshot(only=None) -> dict:
    """only: None = all collectors, "name" = one, ["a","b"] = a subset (live.py fast tier).
    An empty list means zero collectors (returns {}), not the full fleet; unknown names in a
    list are reported once in _errors instead of spawning a doomed subprocess."""
    snap = {}
    if only is not None and not isinstance(only, str):
        want = [(n, HERE / "collectors" / f"{n}.py") for n in sorted(only)]
        files = [str(p) for n, p in want if p.exists()]
        for n, p in want:
            if not p.exists():
                snap.setdefault("_errors", []).append(f"{n}: unknown collector")
    else:
        pattern = str(HERE / "collectors" / (f"{only}.py" if only else "*.py"))
        files = sorted(glob.glob(pattern))
    files = [f for f in files
             if not pathlib.Path(f).name.startswith("_")]   # _*.py = shared libs, not collectors
    if not files:
        return snap

    def run_one(f):
        # -P keeps collectors/ off the child's sys.path so usb.py/power.py can't shadow pip pkgs
        return subprocess.run([sys.executable, "-P", f],
                              capture_output=True, text=True, timeout=25).stdout

    with ThreadPoolExecutor(max_workers=min(8, len(files) or 1)) as ex:
        for f, fut in [(f, ex.submit(run_one, f)) for f in files]:
            try:
                snap.update(json.loads(fut.result()))    # collectors namespace their own keys
            except Exception as e:
                snap.setdefault("_errors", []).append(f"{pathlib.Path(f).name}: {e}")
    return snap


def exit_code_for(findings) -> int:
    """Machine-consumable severity: 0 = clean, 1 = WARN only, 2 = CRIT present. Lets Task
    Scheduler / CI / scripts detect machine distress without parsing stdout."""
    levels = {f.get("level") for f in findings if isinstance(f, dict)}
    if "CRIT" in levels:
        return 2
    if "WARN" in levels:
        return 1
    return 0


def print_findings(snap):
    import rules
    findings = rules.diagnose(snap)
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
        return findings
    order = {"CRIT": 0, "WARN": 1}
    for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
        print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
              + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))
    return findings


def narrate():
    import schema, infer
    snap = snapshot()
    bundle = infer.load()                                   # loads ckpt.pt + vocab.json
    print(infer.generate_report(bundle, schema.serialize_metrics(snap)))
    print("\n--- findings (truth) ---")
    print_findings(snap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="diag", help="diag | net | report | discover")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--spawn", action="store_true", help="discover: write stub collectors")
    args = ap.parse_args()

    if args.cmd == "discover":
        import discover
        discover.main(spawn=args.spawn)
        return
    if args.cmd == "report" and not args.no_llm:
        narrate()
        return
    snap = snapshot(only="net" if args.cmd == "net" else None)
    if args.json:
        print(json.dumps(snap, indent=2))
        return 0
    import rules
    findings = rules.diagnose(snap)
    # reuse print_findings for the human output, then exit with a severity-coded status
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
    else:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
                  + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))
    return exit_code_for(findings)


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main() or 0)
```

### `history.py`

```python
# history.py — append one snapshot to a SQLite history DB. Run on a timer (Task Scheduler).
# One row = timestamp + host + the full snapshot JSON. The host column lets the History graph and
# the Search feature tell machines apart; an index on (host, ts) keeps queries fast as it grows.
# DB path is overridable via WATCHTOWER_HISTORY_DB (used by the exam to stay hermetic).
import sqlite3, json, time, os, pathlib, socket
import sysdiag

DB = pathlib.Path(os.environ.get("WATCHTOWER_HISTORY_DB")
                  or (pathlib.Path(__file__).parent / "history.db"))
RETAIN_DAYS = int(os.environ.get("WATCHTOWER_HISTORY_RETAIN_DAYS", "0"))   # 0 = keep everything


def _ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS snapshots (ts TEXT, host TEXT, json TEXT)")
    # migrate a pre-host table (older rows have no host column) BEFORE indexing on host
    cols = [r[1] for r in con.execute("PRAGMA table_info(snapshots)").fetchall()]
    if "host" not in cols:
        con.execute("ALTER TABLE snapshots ADD COLUMN host TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS ix_snap_host_ts ON snapshots(host, ts)")


def main():
    snap = sysdiag.snapshot()                        # runs the collectors (local sensors)
    host = snap.get("_host") or socket.gethostname()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with sqlite3.connect(DB) as con:
        _ensure(con)
        con.execute("INSERT INTO snapshots(ts, host, json) VALUES (?, ?, ?)",
                    (ts, host, json.dumps(snap)))
        if RETAIN_DAYS > 0:
            cutoff = time.strftime("%Y-%m-%dT%H:%M:%S",
                                   time.localtime(time.time() - RETAIN_DAYS * 86400))
            con.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
    print("logged", ts, host)


if __name__ == "__main__":
    main()
```

### `live.py`

```python
# live.py — background sampler feeding the GUI's live graphs and the chat brain.
# Two tiers: FAST collectors every FAST_S seconds, the FULL fleet every FULL_S — so the
# dashboard stays live without spawning 19 processes (10 of them PowerShell) every tick.
# In-memory ring buffer only (~1h); long-term history stays with history.py/Task Scheduler.
#
# REMOTE mode (WATCHTOWER_REMOTE=1): instead of sampling THIS machine, run an HTTP
# receiver and let monitored machines push snapshots in (ship.py -> NiFi -> /ingest).
# Each host gets its OWN ring/snapshot/stamps, keyed by the host name in the payload;
# the GUI's host selector picks which one the panel/graphs/chat read (see _focus).
import hmac, json, os, socket, threading, time, collections
import pandas as pd
import sysdiag

REMOTE = os.environ.get("WATCHTOWER_REMOTE") == "1"
LOCAL_HOST = socket.gethostname()
FAST_S, FULL_S = 5, 60
FAST = ["cpu", "gpu", "mem", "sensors", "disk"]     # cheap collectors, safe at 5s cadence
KEEP = 3600 // FAST_S                               # ~1h of points
MAX_HOSTS = 256                                     # cap distinct reporters — one authenticated
#                                                    agent minting unlimited host names must not
#                                                    grow _hosts (each ~a 1h ring) without bound

# Friendly label -> path into the snapshot (superset of trends.METRICS: the deep keys too)
METRICS = {
    "CPU temp (C)":     ("sensors", "cpu_temp"),
    "CPU load (%)":     ("cpu", "load"),
    "CPU clock (MHz)":  ("cpu", "mhz"),
    "GPU temp (C)":     ("gpu", "temp"),
    "GPU power (W)":    ("gpu", "power"),
    "GPU util (%)":     ("gpu", "util"),
    "GPU VRAM (%)":     ("gpu", "vram_pct"),
    "GPU fan (%)":      ("gpu", "fan_pct"),
    "GPU clock (MHz)":  ("gpu", "sm_mhz"),
    "Liquid temp (C)":  ("sensors", "liquid_temp"),
    "Pump (RPM)":       ("sensors", "pump_rpm"),
    "RAM used (%)":     ("mem", "pct"),
    "Disk C used (%)":  ("disk", "C"),
    "Ping (ms)":        ("net", "ping_ms"),
    "DNS (ms)":         ("net", "dns_ms"),
    "WHEA errors":      ("whea", "recent_errors"),
    "VMs running":      ("vm", "running"),
    "Services failed":  ("services", "failed"),
    "Services running": ("services", "running"),
    "SSH targets down": ("ssh", "down"),
}
# labels backed by FAST-tier collectors get a fresh point every tick; the rest only when
# the full fleet runs — recording them per-tick would fake 12 duplicate samples per real one
FAST_LABELS = {lbl for lbl, path in METRICS.items() if path[0] in FAST}

_lock = threading.Lock()
_hosts: dict = {}                                   # host name -> per-host state (see _new_host)
_focus = None                                       # host the panel/graphs/chat currently read
_thread = None


def _new_host():
    return {"snap": {}, "stamp": 0.0, "full_stamp": 0.0,
            "errs": {"fast": [], "full": []}, "buf": collections.deque(maxlen=KEEP)}


def _dig(snap, path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _record(fresh, merge, host, extra=None):
    """Fold one snapshot into `host`'s ring. `merge` True = fast partial (keep prior full-tier
    keys), False = full replace. `extra` (label/tags from a remote payload) is stamped in."""
    errs = fresh.pop("_errors", [])
    if not isinstance(errs, list):        # semi-trusted remote JSON: a non-list _errors must not
        errs = [str(errs)]                # crash _record (it's summed with the other tier's list)
    now = time.time()
    with _lock:
        if host not in _hosts and len(_hosts) >= MAX_HOSTS:
            return                              # cardinality cap reached — ignore new reporters
        st = _hosts.get(host) or _hosts.setdefault(host, _new_host())
        if merge:                                   # fast tier: authoritative for its own errors
            st["errs"]["fast"] = errs
            st["snap"] = {**st["snap"], **fresh}
            labels = FAST_LABELS
        else:                                       # full fleet: authoritative for everything
            st["errs"]["fast"], st["errs"]["full"] = [], errs
            st["snap"] = fresh
            st["full_stamp"] = now
            labels = METRICS.keys()
        st["snap"]["_host"] = host                  # identity is always present, param wins
        for k, v in (extra or {}).items():
            st["snap"][k] = v
        combined = st["errs"]["fast"] + st["errs"]["full"]
        st["snap"].pop("_errors", None)
        if combined:
            st["snap"]["_errors"] = combined
        st["stamp"] = now
        st["buf"].append((now, {lbl: _dig(st["snap"], METRICS[lbl]) for lbl in labels}))


def _loop():
    last_full = time.time()                          # start() already took the first full
    while True:
        t0 = time.time()
        try:
            if t0 - last_full >= FULL_S:
                _record(sysdiag.snapshot(), merge=False, host=LOCAL_HOST)
                last_full = t0
            else:
                _record(sysdiag.snapshot(only=FAST), merge=True, host=LOCAL_HOST)
        except Exception:
            pass    # a transient failure (or interpreter shutdown race) must not kill the
        #             sampler for the rest of the app's life; the next tick retries
        time.sleep(max(0.5, FAST_S - (time.time() - t0)))


def start():
    """Idempotent. Takes one synchronous FULL snapshot so the first paint has data."""
    global _thread, _focus
    if _thread and _thread.is_alive():
        return
    _record(sysdiag.snapshot(), merge=False, host=LOCAL_HOST)
    _focus = LOCAL_HOST
    _thread = threading.Thread(target=_loop, daemon=True, name="live-sampler")
    _thread.start()


def start_receiver(bind=None, token=None):
    """REMOTE mode: accept snapshots pushed by ship.py (directly or via NiFi InvokeHTTP).
    POST /ingest, JSON {host, label?, tags?, partial, snap}; X-Watchtower-Token must match.
    Each distinct `host` gets its own ring. Merge is per-collector (top-level keys replace
    wholesale), so a partial payload must carry COMPLETE collector objects — ship.py does."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    bind = bind or os.environ.get("WATCHTOWER_INGEST_BIND", "0.0.0.0:7861")
    token = token or os.environ.get("WATCHTOWER_TOKEN", "")
    if not token:
        raise ValueError("REMOTE mode needs WATCHTOWER_TOKEN set — refusing an open listener")
    host, port = bind.rsplit(":", 1)

    class Ingest(BaseHTTPRequestHandler):
        def _reply(self, code, msg=b""):
            self.send_response(code)
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

        def do_POST(self):
            if self.path != "/ingest":
                return self._reply(404)
            try:
                # header parses are inside the try: a non-ASCII token or non-numeric
                # Content-Length must return a clean 4xx, not raise + reset the connection
                got = self.headers.get("X-Watchtower-Token", "")
                if not hmac.compare_digest(got.encode(), token.encode()):
                    return self._reply(403)
                n = int(self.headers.get("Content-Length") or 0)
                if not 0 < n <= 2_000_000:                   # a snapshot is ~50KB; cap abuse
                    return self._reply(413)
                p = json.loads(self.rfile.read(n))
                snap = p["snap"]
                if not isinstance(snap, dict):
                    raise TypeError("snap must be an object")
            except Exception:
                return self._reply(400, b"bad payload")
            reporter = str(p.get("host", "?"))[:64]           # identity of the monitored box
            extra = {"_label": str(p.get("label", ""))[:128],
                     "_tags": p.get("tags") if isinstance(p.get("tags"), dict) else {}}
            _record(snap, merge=bool(p.get("partial")), host=reporter, extra=extra)
            self._reply(200, b"ok")

        def log_message(self, *_):                            # quiet: 12 req/min/host is not news
            pass

    srv = ThreadingHTTPServer((host, int(port)), Ingest)
    threading.Thread(target=srv.serve_forever, daemon=True, name="live-ingest").start()
    return srv


# ---- read side: everything below picks a host (explicit arg, else focus, else the only one) ----

def hosts():
    """Sorted list of hosts we've received data from (for the GUI selector)."""
    with _lock:
        return sorted(_hosts)


def set_focus(host):
    """The host the chat brain answers about (the GUI host selector sets this)."""
    global _focus
    if host and host in _hosts:
        _focus = host


def get_focus():
    return _focus


def _resolve(host):
    if host and host in _hosts:
        return host
    if _focus and _focus in _hosts:
        return _focus
    hs = sorted(_hosts)
    return hs[0] if hs else None


def get_latest(host=None):
    """-> (snapshot, fast_age_s, full_age_s) for one host. Empty dict + inf/inf if none."""
    now = time.time()
    with _lock:
        st = _hosts.get(_resolve(host))
        if not st:
            return {}, float("inf"), float("inf")
        return (dict(st["snap"]),
                now - st["stamp"] if st["stamp"] else float("inf"),
                now - st["full_stamp"] if st["full_stamp"] else float("inf"))


SPANS = {"5 min": 5, "15 min": 15, "60 min": 60}


def frame(labels, span="15 min", host=None):
    """Long-form DataFrame (time, value, series) for one host's metrics — LinePlot food."""
    cutoff = time.time() - SPANS.get(span, 15) * 60
    labels = [l for l in (labels or []) if l in METRICS]
    with _lock:
        st = _hosts.get(_resolve(host))
        rows = [(ts, vals) for ts, vals in st["buf"] if ts >= cutoff] if st else []
    t, v, s = [], [], []
    for ts, vals in rows:
        for lbl in labels:
            if vals.get(lbl) is not None:
                t.append(ts)
                v.append(vals[lbl])
                s.append(lbl)
    return pd.DataFrame({"time": pd.to_datetime(t, unit="s"), "value": v, "series": s})


def deltas(minutes=10, host=None):
    """Compact per-metric trend text for the LLM: 'CPU temp (C): 45 -> 52 (min 44, max 53)'."""
    cutoff = time.time() - minutes * 60
    with _lock:
        st = _hosts.get(_resolve(host))
        rows = [vals for ts, vals in st["buf"] if ts >= cutoff] if st else []
    lines = []
    for lbl in METRICS:
        seq = [r[lbl] for r in rows if r.get(lbl) is not None]
        if len(seq) >= 2 and (min(seq) != max(seq) or seq[0] != seq[-1]):
            lines.append(f"{lbl}: {seq[0]} -> {seq[-1]} (min {min(seq)}, max {max(seq)}, n={len(seq)})")
        elif seq:
            lines.append(f"{lbl}: steady at {seq[-1]} (n={len(seq)})")
    return "\n".join(lines)


def demo():  # the one runnable check: multi-host rings stay separate and frame() shapes them
    # two synthetic hosts pushed straight in (no network) — rings must not cross-contaminate
    _record({"cpu": {"load": 10}, "sensors": {"cpu_temp": 40}}, merge=False, host="HOST-A")
    _record({"cpu": {"load": 90}, "sensors": {"cpu_temp": 80}}, merge=False, host="HOST-B")
    assert hosts() == ["HOST-A", "HOST-B"], hosts()
    a, _, _ = get_latest("HOST-A")
    b, _, _ = get_latest("HOST-B")
    assert a["sensors"]["cpu_temp"] == 40 and b["sensors"]["cpu_temp"] == 80, "rings crossed"
    assert a["_host"] == "HOST-A", "host identity missing"
    set_focus("HOST-B")
    f, _, _ = get_latest()                       # no arg -> focus
    assert f["_host"] == "HOST-B", "focus not honoured"
    df = frame(["CPU load (%)"], "5 min", host="HOST-A")
    assert list(df.columns) == ["time", "value", "series"] and (df["value"] == 10).all()
    # and the real local sampler still works end to end
    _hosts.clear()
    start()
    time.sleep(FAST_S + 2)
    snap, age, full_age = get_latest()
    assert snap and age < FAST_S + 3 and full_age < FULL_S + 30, (age, full_age)
    assert snap["_host"] == LOCAL_HOST, "local host identity"
    print(f"live ok — hosts isolated, focus works, local sampler live ({LOCAL_HOST}, age {age:.1f}s)")


if __name__ == "__main__":
    demo()
```

### `trends.py`

```python
# trends.py — read history.db and return time-series DataFrames for the UI graphs.
# history.db is filled by the Task Scheduler logger (history.py); this only reads it.
import json, sqlite3, os, pathlib
import pandas as pd

DB = pathlib.Path(os.environ.get("WATCHTOWER_HISTORY_DB")
                  or (pathlib.Path(__file__).parent / "history.db"))

# Friendly label -> path into a snapshot dict.
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

# How many recent collection runs to plot. Data is run-based (every ~15 min), not
# continuous, so we select by run count, not calendar range.
RUNS = {"Last 10 runs": 10, "Last 25 runs": 25, "Last 50 runs": 50,
        "Last 100 runs": 100, "All runs": None}


def _dig(snap, path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def series(metric, runs_label="Last 25 runs", host=None):
    path = METRICS.get(metric)
    if path is None or not DB.exists():
        return pd.DataFrame({"time": [], "value": [], "when": []})
    limit = RUNS.get(runs_label)
    where, params = "", []
    if host:
        where = " WHERE host = ?"
        params.append(host)
    query = f"SELECT ts, json FROM snapshots{where} ORDER BY ts DESC"
    if limit:
        query += f" LIMIT {int(limit)}"   # int() guards the f-string against injection
    with sqlite3.connect(DB) as con:      # close the handle (the Gradio app renders many graphs)
        try:
            rows = con.execute(query, params).fetchall()
        except sqlite3.OperationalError:
            rows = con.execute(query.replace(where, ""), []).fetchall()  # pre-host DB: no host col
    rows.reverse()  # DESC fetch gives newest-first; flip to oldest->newest for the line
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
    when = [x.strftime("%b %d, %H:%M:%S") for x in t]  # date + time, shown on hover
    return pd.DataFrame({"time": t, "value": values, "when": when})


if __name__ == "__main__":
    df = series("CPU temp (C)", "Last 10 runs")
    assert list(df.columns) == ["time", "value", "when"] and len(df) <= 10
    print(df.tail())
```

### `search.py`

```python
# search.py — search the logged history by COMPONENT, by COMPUTER (host), and by DATE/TIME.
# Reads the same history.db that history.py writes (path overridable via WATCHTOWER_HISTORY_DB).
# A "component" is matched as a case-insensitive substring against each metric's dotted path
# (e.g. "cpu_temp" -> sensors.cpu_temp, "gpu" -> every gpu.* metric, "temp" -> all temperatures),
# so you can search broad or narrow. Returns flat rows {ts, host, metric, value} — READ ONLY.
import sqlite3, json, os, pathlib

DB = pathlib.Path(os.environ.get("WATCHTOWER_HISTORY_DB")
                  or (pathlib.Path(__file__).parent / "history.db"))


def _flatten(snap, prefix=""):
    """Yield (dotted_path, scalar_value) for every scalar leaf; skip private _keys and containers
    (the value we plot/search is always a scalar)."""
    for k, v in snap.items():
        if str(k).startswith("_"):
            continue
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from _flatten(v, path + ".")
        elif isinstance(v, (int, float, str, bool)) or v is None:
            yield path, v
        # lists (containers/drives) are skipped — search targets scalar metrics


def search(component=None, host=None, since=None, until=None, limit=2000):
    """Rows matching all supplied filters, newest first.
      component  case-insensitive substring of the metric's dotted path (None = all metrics)
      host       exact machine name (None = all)
      since/until  ISO 'YYYY-MM-DDThh:mm:ss' bounds on the snapshot timestamp (inclusive)
    """
    if not DB.exists():
        return []
    if component is not None:
        component = str(component)[:200]      # cap: a metric path is short; a huge string would
        #                                       turn the per-row substring scan into a DoS
    # keep the time bounds separate from the host bound: a pre-host-column DB must still honor
    # since/until (the fallback below drops ONLY the host clause, never the time window).
    ts_where, ts_params = [], []
    if since is not None:
        ts_where.append("ts >= ?"); ts_params.append(since)
    if until is not None:
        ts_where.append("ts <= ?"); ts_params.append(until)
    where, params = list(ts_where), list(ts_params)
    if host is not None:
        where.insert(0, "host = ?"); params.insert(0, host)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    ts_clause = (" WHERE " + " AND ".join(ts_where)) if ts_where else ""
    comp = component.lower() if component else None
    out = []
    with sqlite3.connect(DB) as con:
        try:
            rows = con.execute(f"SELECT ts, host, json FROM snapshots{clause} ORDER BY ts DESC",
                               params).fetchall()
        except sqlite3.OperationalError:
            # pre-host DB (no host column): drop ONLY the host filter, keep the time window;
            # the host filter is then re-applied per-row from the snapshot's own _host below.
            rows = con.execute(f"SELECT ts, json FROM snapshots{ts_clause} ORDER BY ts DESC",
                               ts_params).fetchall()
            rows = [(ts, None, j) for ts, j in rows]
    for row in rows:
        ts, h, j = row
        try:
            snap = json.loads(j)
        except Exception:
            continue
        h = h or snap.get("_host") or "?"
        if host is not None and h != host:
            continue
        for path, value in _flatten(snap):
            if comp is None or comp in path.lower():
                out.append({"ts": ts, "host": h, "metric": path, "value": value})
                if len(out) >= limit:
                    return out
    return out


def components(host=None, limit=500):
    """The distinct metric paths present in history — for a search-UI dropdown."""
    seen = {}
    for r in search(host=host, limit=limit * 40):
        seen[r["metric"]] = None
    return sorted(seen)


def demo():  # the one runnable check (uses a temp DB seeded with two hosts)
    import tempfile, time
    p = pathlib.Path(tempfile.mkdtemp()) / "h.db"
    os.environ["WATCHTOWER_HISTORY_DB"] = str(p)
    global DB
    DB = p
    with sqlite3.connect(p) as con:
        con.execute("CREATE TABLE snapshots (ts TEXT, host TEXT, json TEXT)")
        con.execute("INSERT INTO snapshots VALUES (?,?,?)",
                    ("2026-07-02T10:00:00", "PC-A", json.dumps({"sensors": {"cpu_temp": 55}, "gpu": {"temp": 60}})))
        con.execute("INSERT INTO snapshots VALUES (?,?,?)",
                    ("2026-07-02T11:00:00", "PC-B", json.dumps({"sensors": {"cpu_temp": 70}})))
    assert len(search(component="cpu_temp")) == 2, "component search"
    assert len(search(component="cpu_temp", host="PC-A")) == 1, "host filter"
    assert len(search(component="cpu_temp", host="nope")) == 0, "host miss"
    assert len(search(component="temp")) == 3, "substring matches cpu_temp + gpu.temp"
    assert len(search(component="cpu_temp", until="2026-07-02T10:30:00")) == 1, "time window"
    assert all({"ts", "host", "metric", "value"} <= set(r) for r in search(component="cpu")), "row shape"
    print("search ok")


if __name__ == "__main__":
    demo()
```

### `notes.py`

```python
# notes.py — shared operator notes for the Watch Tower dashboard. Multiple people using the same
# instance can leave a note ("rebooted the NAS", "GPU RMA pending") that everyone else sees. Plain
# SQLite so it persists across restarts and across processes; no new pip deps. READ + APPEND only,
# never executed. DB path overridable via WATCHTOWER_NOTES_DB (the exam uses this to stay hermetic).
import sqlite3, os, time, pathlib

DB = pathlib.Path(os.environ.get("WATCHTOWER_NOTES_DB")
                  or (pathlib.Path(__file__).parent / "notes.db"))
MAX_TEXT = 10_000          # a note is a sentence or three, not a document
MAX_USER = 64


def _con():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS notes (ts TEXT, user TEXT, text TEXT, host TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_notes_ts ON notes(ts)")
    return con


def add_note(user: str, text: str, host: str = "") -> dict:
    """Append one note. Raises ValueError on empty text or over-length input (a trust boundary:
    the note comes from a browser form)."""
    user = (str(user).strip() or "anonymous")[:MAX_USER]
    text = str(text).strip()
    if not text:
        raise ValueError("note text is empty")
    if len(text) > MAX_TEXT:
        raise ValueError(f"note too long ({len(text)} > {MAX_TEXT} chars)")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _con() as con:
        con.execute("INSERT INTO notes(ts, user, text, host) VALUES (?, ?, ?, ?)",
                    (ts, user, text, str(host)[:MAX_USER]))
    return {"ts": ts, "user": user, "text": text, "host": str(host)[:MAX_USER]}


def list_notes(limit: int = 200) -> list[dict]:
    """Most recent notes first."""
    if not DB.exists():
        return []
    with _con() as con:
        rows = con.execute("SELECT ts, user, text, host FROM notes ORDER BY ts DESC LIMIT ?",
                           (int(limit),)).fetchall()
    return [{"ts": ts, "user": u, "text": t, "host": h} for ts, u, t, h in rows]


def demo():  # the one runnable check
    import tempfile
    os.environ["WATCHTOWER_NOTES_DB"] = str(pathlib.Path(tempfile.mkdtemp()) / "t.db")
    global DB
    DB = pathlib.Path(os.environ["WATCHTOWER_NOTES_DB"])
    n = add_note("alice", "rebooted the NAS")
    assert n["user"] == "alice" and any(x["text"] == "rebooted the NAS" for x in list_notes())
    try:
        add_note("bob", "x" * (MAX_TEXT + 1)); assert False, "over-length must raise"
    except ValueError:
        pass
    try:
        add_note("bob", "   "); assert False, "empty must raise"
    except ValueError:
        pass
    print("notes ok")


if __name__ == "__main__":
    demo()
```

### `context.py`

```python
import json, pathlib
import rules
import rag

FACTS = pathlib.Path(__file__).parent / "system_facts.md"


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _snapshot(host=None) -> dict:
    # prefer the live sampler's cache (fresh within ~3 ticks) — a chat message then costs
    # zero collector runs; fall back to a one-shot snapshot when the sampler isn't running
    # (CLI chat.py, sysdiag report) so behavior there is unchanged. `host` selects which
    # machine's cache to read (the GUI passes the selected host explicitly, so concurrent
    # tabs viewing different hosts never clobber each other via a shared global).
    try:
        import live
        snap, age, full_age = live.get_latest(host)
        # REMOTE mode: the cache is the ONLY truth — falling back to local collectors
        # would silently describe the monitoring computer instead of the monitored one.
        if live.REMOTE:
            if not snap:
                return {"_note": "remote mode: no snapshots received from the agent yet"}
            out = {**snap, "_snapshot_age_s": round(min(age, 9999), 1),
                   "_full_fleet_age_s": round(min(full_age, 9999), 1)}
            if age > 3 * live.FAST_S:
                out["_note"] = f"agent stopped shipping {round(age)}s ago — data is STALE"
            return out
        if snap and age < 3 * live.FAST_S:
            return {**snap, "_snapshot_age_s": round(age, 1),
                    "_full_fleet_age_s": round(min(full_age, 9999), 1)}
    except Exception:
        pass
    try:
        import sysdiag
        return sysdiag.snapshot()
    except Exception as e:
        return {"_note": f"truth layer not built ({e}); showing stub.",
                "cpu": {"load": 0}, "sensors": {"cpu_temp": 0}, "mem": {"pct": 0},
                "gpu": {"util": 0, "temp": 0, "power": 0, "vram_pct": 0},
                "disk": {"C": 0}, "whea": {"recent_errors": 0}}


def snapshot_and_findings(host=None):
    snap = _snapshot(host)
    try:
        return snap, rules.diagnose(snap)
    except Exception as e:
        # REMOTE snapshots are semi-trusted JSON from another machine; a malformed field
        # must not crash the 5s GUI panel / chat. Degrade to a single visible finding.
        return snap, [{"level": "WARN", "what": "rules engine",
                       "value": f"could not evaluate snapshot: {e}", "limit": "", "unit": ""}]


def build(message: str = "", host=None) -> str:
    snap, findings = snapshot_and_findings(host)
    age, full_age = snap.get("_snapshot_age_s"), snap.get("_full_fleet_age_s")
    label = ("LIVE SNAPSHOT (JSON, just collected):" if age is None else
             f"LIVE SNAPSHOT (JSON; fast metrics ~{age}s old, "
             f"full fleet — net/docker/whea/power/storage — ~{full_age}s old):")
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        label,
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    try:                                   # live trend digest, when the sampler is running
        import live
        trend = live.deltas(host=host)
        if trend:
            parts += ["", "RECENT TRENDS (live-sampled, last 10 min):", trend]
    except Exception:
        pass
    refs = rag.context_block(message)      # semantic retrieval replaces the keyword gate
    if refs:
        parts += ["", refs]
    return "\n".join(parts)

if __name__ == "__main__":
    out = build("how is my reverse proxy set up?")
    assert "FINDINGS" in out, "context block lost its findings"
    print(out[:800])
```

### `rag.py`

```python
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
# mxbai-embed-large (1024-dim) measured best on this repo's frozen QA set: hit@5 0.939 / MRR@5
# 0.792, a strict win over nomic-embed-text (0.909 / 0.774) on BOTH recall and ranking. Swap back
# to "nomic-embed-text" (768-dim, ~270 MB, faster) if VRAM/pull size matters — retrieval degrades
# only slightly. A model change rebuilds the index automatically (settings hash below).
EMBED_MODEL  = "mxbai-embed-large"               # `ollama pull mxbai-embed-large` (~670 MB, CPU-ok)
EMBED_BATCH  = 64                                # chunks sent per /api/embed request
HERE = pathlib.Path(__file__).parent
DB   = HERE / "rag_index.db"                     # generated cache — git-ignored

# Docs to make searchable: EVERY *.md in this folder, plus the homelab notes (if present). Missing
# files are skipped. Drop a new .md in here and the next `python rag.py --build` picks it up.
# Project meta-docs (this RSI log, the recreate/instruction guides) are NOT reference material —
# excluded so they don't dilute a hardware/troubleshooting query.
_EXCLUDE = {"RSI-REPORT.md"}
SOURCES = [pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md",
           *[p for p in sorted(HERE.glob("*.md")) if p.name not in _EXCLUDE]]

# --- tuning knobs (the RAG equivalent of rules.THRESH — tune for YOUR docs) ---
# 1600/400 measured best with mxbai on this corpus (see the model note above). Larger chunks then
# hurt (facts get averaged out); smaller ones split answers across chunk boundaries.
CHUNK_CHARS = 1600    # size of each searchable slice (~400 tokens)
OVERLAP     = 400     # chars repeated between neighbours so a fact on a boundary isn't lost
TOP_K       = 4       # how many chunks to return per question
MIN_SCORE   = 0.45    # cosine floor; below this a chunk is "not really relevant" and is dropped
                      #   -> an off-topic question retrieves nothing. THIS is the knob to tune.

# mxbai-embed-large wants a query-side instruction and NO document prefix. (nomic-embed-text
# instead wants "search_document: " / "search_query: " — swap both if you switch back.)
DOC_PREFIX   = ""
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


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


# --- hybrid rerank: fetch a larger vector pool, then re-rank by cosine + how much the chunk's
# vocabulary overlaps the QUESTION (a BM25-style lexical signal). Measured on this repo's frozen
# 33-QA set: MRR@5 0.79 -> 0.95, hit@5 0.94 -> 0.97 — the answer passage both embeds near AND
# shares words with the question, and lexical overlap breaks ties the embedding alone gets wrong.
RERANK_POOL  = 20     # vector candidates to rerank (>= k)
RERANK_ALPHA = 0.6    # weight on cosine; (1-alpha) on lexical overlap. 0.5-0.7 all optimal here.
_WORD = re.compile(r"[a-z0-9]{3,}")
_STOP = frozenset(("the and for with your you are that this how what when where can does from into "
                   "will would should could have has had not but they them then than").split())


def _lex_overlap(query: str, text: str) -> float:
    qw = set(_WORD.findall(query.lower())) - _STOP
    if not qw:
        return 0.0
    return len(qw & set(_WORD.findall(text.lower()))) / len(qw)


def _knn(con, question: str, k: int):
    """The k best chunks as [(cosine_score, source, text), ...], hybrid-reranked (vector + lexical).
    The returned score is still the cosine (so retrieve()'s min_score floor is unchanged); only the
    ORDER reflects the hybrid rank. Empty if the corpus is empty."""
    q = serialize_float32(_embed(question, QUERY_PREFIX))
    pool = max(k, RERANK_POOL)
    try:
        rows = con.execute(
            "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (q, pool),
        ).fetchall()
    except sqlite3.OperationalError:
        return []                    # no vec_chunks table -> nothing indexed
    out = []
    for rowid, dist in rows:
        score = 1.0 - (dist * dist) / 2.0    # L2 on UNIT vectors -> cosine (vectors are normalized)
        src, txt = con.execute("SELECT source, text FROM chunks WHERE id = ?", (rowid,)).fetchone()
        out.append((score, src, txt))
    out.sort(key=lambda r: -(RERANK_ALPHA * r[0] + (1.0 - RERANK_ALPHA) * _lex_overlap(question, r[2])))
    return out[:k]


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
```

### `art.py`

```python
# art.py — the Watch Tower banner, shared by the CLI (chat.py) and the web UI (app.py).
import os, shutil

if os.name == "nt":
    os.system("")   # enable ANSI in legacy Windows consoles; no-op in Windows Terminal

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
    """Print the banner in light blue with a full-width rule under it (terminal)."""
    width = shutil.get_terminal_size((100, 20)).columns
    try:
        print(f"{LIGHT_BLUE}{WATCH_TOWER}\n{'─' * width}{RESET}")
    except UnicodeEncodeError:      # redirected/cp1252 stdout can't draw box glyphs —
        print("WATCH TOWER")        # a cosmetic banner must never kill the app


def html_banner():
    """Return the banner as HTML for Gradio: monospace <pre>, light blue, scrolls if narrow."""
    return ('<pre style="color:#ADD8E6; line-height:1.05; font-size:11px; '
            'overflow-x:auto; margin:0; white-space:pre">' + WATCH_TOWER + '</pre>')


if __name__ == "__main__":
    cli_banner()
```

### `app.py`

```python
"""app.py — Watch Tower: live stats, chat, history graphs, search, and shared notes.
READ-ONLY, 127.0.0.1 only."""
import html
import gradio as gr
import schema, brain, context, art, trends, live, search, notes


def _md_safe(s) -> str:
    """Neutralize markdown/HTML in user- or remote-supplied text before it hits gr.Markdown.
    Notes and remote label/tags/_note are prose shown to OTHER users of the dashboard, so an
    unescaped `<img onerror=…>` or `[x](javascript:…)` would be stored XSS. HTML-escape kills the
    raw-HTML vector; escaping the markdown link/emphasis metacharacters kills the rest."""
    out = html.escape(str(s), quote=True)
    for ch in "[]()`*_~":
        out = out.replace(ch, "\\" + ch)
    return out

if gr.NO_RELOAD:   # guard: `gradio app.py` reload mode re-imports modules — without this,
    #              every source edit would leak one more immortal sampler thread.
    if live.REMOTE:
        live.start_receiver()   # monitoring another machine: data arrives via ship.py/NiFi
    else:
        live.start()            # monitoring THIS machine: local two-tier sampler
#                Background sampler: fast metrics every 5s, full fleet every 60s. The stats
#                panel, live graphs AND the chat brain all read its cache — nothing in the
#                UI spawns the collector fleet per tick anymore.


WAITING = "(waiting for data)"


def refresh_hosts(current):
    """Keep the host selector's choices current and point the chat at the visible host.
    In local mode this is a single host; in remote mode new agents appear here live."""
    hs = live.hosts()
    if not hs:
        return gr.update(choices=[WAITING], value=WAITING)
    val = current if current in hs else hs[0]
    live.set_focus(val)                     # the chat brain answers about the selected host
    return gr.update(choices=hs, value=val)


def stats_md(host) -> str:
    live.set_focus(host)                    # default for the host=None fallback path (CLI chat)
    snap, findings = context.snapshot_and_findings(host)   # explicit host: no cross-tab clobber
    head = schema.summarize(snap)
    # _host/_label/_tags/_note come from a remote agent's payload (semi-trusted); escape them and
    # the finding text before they hit gr.Markdown so a hostile payload can't inject stored XSS.
    ident = _md_safe(snap.get("_host", host))
    label = snap.get("_label")
    age = snap.get("_snapshot_age_s")
    fresh = f" *(sampled {age}s ago)*" if age is not None else ""
    title = f"### {ident}" + (f" — {_md_safe(label)}" if label else "") + fresh
    lines = [f"{title}\n{head}", "", "### Findings"]
    if findings:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            lines.append(f"- **[{f['level']}]** {_md_safe(f['what'])}: {_md_safe(f['value'])}{_md_safe(f['unit'])}")
    else:
        lines.append("- OK — no findings")
    d = snap.get("docker", {})
    if d and "error" not in d:
        lines.append(f"\n**Docker:** {d.get('running')}/{d.get('total')} running")
    tags = snap.get("_tags")
    if isinstance(tags, dict) and tags:
        lines.append("\n" + " · ".join(f"`{_md_safe(k)}={_md_safe(v)}`" for k, v in tags.items()))
    if "_note" in snap:
        lines.append(f"\n> {_md_safe(snap['_note'])}")
    return "\n".join(lines)


def plot(metric, rng, host):
    # History is per-host too (history.py stamps the host); None/"" host = all machines
    return trends.series(metric, rng, host=host if host and host != WAITING else None)


# ---- Search: by component, by computer, by date/time ----
def do_search(component, host, since, until):
    h = host if host and host not in ("(any)", WAITING) else None
    rows = search.search(component=(component or None), host=h,
                         since=(since or None), until=(until or None), limit=500)
    if not rows:
        return [["(no matches)", "", "", ""]]
    return [[r["ts"], r["host"], r["metric"], r["value"]] for r in rows[:500]]


# ---- Shared notes: any user of this instance can leave one, everyone sees them ----
def render_notes():
    ns = notes.list_notes()
    if not ns:
        return "*No notes yet — be the first to leave one.*"
    return "\n".join(f"- **{_md_safe(n['user'])}** · *{n['ts']}*"
                     + (f" · `{_md_safe(n['host'])}`" if n.get("host") else "")
                     + f"  \n  {_md_safe(n['text'])}"
                     for n in ns)


def post_note(user, text):
    try:
        notes.add_note(user, text, host=live.get_focus() or "")
    except ValueError as e:
        return render_notes() + f"\n\n> ⚠️ {e}", user, text
    return render_notes(), user, ""      # clear the note box, keep the name


_init_hosts = live.hosts()
_init_host = _init_hosts[0] if _init_hosts else WAITING


def live_plot_component(sel, span, host):
    # return a FULL component, not a bare DataFrame: the plot frontend freezes its
    # series/color encoding from the first value it receives, so bare-value updates
    # silently drop any series that wasn't present at page load (e.g. everything,
    # when the page loads seconds after app start). Rebuilding the component each
    # tick re-derives the encoding, so new series appear live.
    return gr.LinePlot(live.frame(sel, span, host=host), x="time", y="value", color="series",
                       title="Live (5s fast tier; net/whea/vm/services every 60s)", height=320)


DEFAULT_SEL = ["CPU temp (C)", "GPU temp (C)", "Liquid temp (C)"]

with gr.Blocks(title="Watch Tower") as app:
    gr.HTML(art.html_banner())
    gr.Markdown("# Watch Tower — your system, explained")
    host_sel = gr.Dropdown(_init_hosts or [WAITING], value=_init_host, label="Host",
                           info="which monitored machine to view (local mode: just this one)")
    with gr.Row():
        with gr.Column(scale=1):
            panel = gr.Markdown(stats_md(_init_host))
            gr.Timer(5).tick(refresh_hosts, inputs=host_sel, outputs=host_sel)
            gr.Timer(5).tick(stats_md, inputs=host_sel, outputs=panel)
        with gr.Column(scale=2):
            gr.ChatInterface(
                fn=brain.ask,
                additional_inputs=[host_sel],   # the selected host reaches brain.ask -> context,
                #                                 so the chat answers about the host you're viewing
                title="Ask about the selected host",
                # list-of-lists (message + each additional input) is required once
                # additional_inputs is set; host is left to default per example
                examples=[["Is anything overheating?"],
                          ["What's eating my disk space?"],
                          ["Are there any hardware errors?"],
                          ["Any failed services or stopped VMs?"]],
            )
    gr.Markdown("## Live graphs")
    with gr.Row():
        live_sel = gr.Dropdown(list(live.METRICS), multiselect=True, label="Metrics",
                               value=DEFAULT_SEL)
        live_span = gr.Dropdown(list(live.SPANS), value="15 min", label="Window")
    live_plot = live_plot_component(DEFAULT_SEL, "15 min", _init_host)
    gr.Timer(5).tick(live_plot_component, inputs=[live_sel, live_span, host_sel], outputs=live_plot)
    live_sel.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)
    live_span.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)
    host_sel.change(stats_md, host_sel, panel)
    host_sel.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)

    gr.Markdown("## History")
    with gr.Row():
        metric = gr.Dropdown(list(trends.METRICS), value="CPU temp (C)", label="Component / metric")
        runs = gr.Dropdown(list(trends.RUNS), value="Last 25 runs", label="Show")
    graph = gr.LinePlot(trends.series("CPU temp (C)", "Last 25 runs", host=_init_host if _init_host != WAITING else None),
                        x="time", y="value", tooltip=["when", "value"],
                        title="History", height=320)
    metric.change(plot, [metric, runs, host_sel], graph)
    runs.change(plot, [metric, runs, host_sel], graph)
    host_sel.change(plot, [metric, runs, host_sel], graph)

    with gr.Accordion("🔎 Search history — by component, computer, or date/time", open=False):
        gr.Markdown("Search every logged snapshot. **Component** is a substring of the metric "
                    "path (`cpu_temp`, `gpu`, `disk`, `docker`…). Leave a field blank for *any*.")
        with gr.Row():
            s_comp = gr.Textbox(label="Component / metric", value="cpu_temp", scale=2)
            s_host = gr.Textbox(label="Computer (host)", placeholder="(any)", scale=1)
            s_since = gr.Textbox(label="Since", placeholder="2026-07-01T00:00:00", scale=1)
            s_until = gr.Textbox(label="Until", placeholder="2026-07-02T23:59:59", scale=1)
        s_btn = gr.Button("Search", variant="primary")
        s_results = gr.Dataframe(headers=["when", "computer", "metric", "value"],
                                 label="Results (newest first, up to 500)", wrap=True)
        s_btn.click(do_search, [s_comp, s_host, s_since, s_until], s_results)

    with gr.Accordion("📝 Shared notes — leave a note for other users of this dashboard", open=False):
        notes_md = gr.Markdown(render_notes())
        with gr.Row():
            n_user = gr.Textbox(label="Your name", placeholder="e.g. alex", scale=1)
            n_text = gr.Textbox(label="Note", placeholder="e.g. RMA'd the NZXT pump — AIO temps are stale",
                                scale=3, lines=1)
        n_btn = gr.Button("Post note", variant="primary")
        n_btn.click(post_note, [n_user, n_text], [notes_md, n_user, n_text])
        gr.Timer(15).tick(render_notes, outputs=notes_md)   # pick up other users' notes live


if __name__ == "__main__":
    import os
    art.cli_banner()
    # port is env-overridable so a second instance (or a remote-monitoring GUI) can run alongside
    # a local one without editing source; default stays 7860.
    port = int(os.environ.get("WATCHTOWER_PORT") or os.environ.get("GRADIO_SERVER_PORT") or 7860)
    try:
        app.launch(server_name="127.0.0.1", server_port=port, inbrowser=True)
    finally:
        import subprocess  # free the model's VRAM on clean exit (Ctrl+C / window close)
        subprocess.run(["ollama", "stop", brain.MODEL], check=False)
```

### `chat.py`

```python
# chat.py — Watch Tower from the command line. Same model + live system context as the web UI.
# Read-only: it advises, it never runs anything. Blank line + Ctrl+C (or type 'exit') to quit.
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

### `ship.py`

```python
# ship.py — run on the MONITORED machine: stream snapshots as JSON to the monitoring
# side, either straight to Watchtower's /ingest or through Apache NiFi (ListenHTTP ->
# InvokeHTTP). Stdlib only — the agent needs collectors/ + sysdiag.py + this file,
# no pip installs. Two-tier cadence: FAST collectors every fast_seconds ({"partial":true}),
# the full fleet every full_seconds.
#
# CUSTOMIZE THE SHIPPED JSON via ship.config.json (see ship.config.example.json):
#   host        identity of THIS machine — how the monitoring side names/selects it
#   label,tags  free-form display label + key/value metadata merged into every payload
#   fast,full   which collectors go in each tier (full: null = the whole fleet)
#   *_seconds   cadence;  narrate: attach the local NanoGPT report to full snapshots
#   url         where to POST
# The identity/destination keys are env-overridable (env wins) so ONE shared config can serve
# many machines by varying just these two on the command line — host via WATCHTOWER_HOST, url
# via WATCHTOWER_SHIP_URL. Other keys (label/tags/fast/full/cadence/narrate) come from the file
# (or --narrate). Also honoured: WATCHTOWER_TOKEN (secret), WATCHTOWER_SHIP_CONFIG (config path).
#
# `python ship.py --narrate` (or "narrate": true) runs the local NanoGPT narrator on each
# FULL snapshot and ships its report as snap["_report"] (needs torch + ckpt.pt here; without
# them the flag degrades to a note and keeps shipping raw metrics).
import json, os, socket, sys, time, urllib.request
import sysdiag

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.environ.get("WATCHTOWER_SHIP_CONFIG", os.path.join(HERE, "ship.config.json"))
    cfg = {}
    try:
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            cfg = {k: v for k, v in loaded.items() if not k.startswith("_")}
        else:
            print("ship.config.json ignored (not a JSON object)")   # a list/number/string
    except FileNotFoundError:
        pass                                    # config is optional; env + defaults suffice
    except (json.JSONDecodeError, OSError) as e:
        print(f"ship.config.json ignored ({e})")
    cfg.setdefault("host", socket.gethostname())
    cfg.setdefault("label", "")
    cfg.setdefault("tags", {})
    cfg.setdefault("fast", ["cpu", "gpu", "mem", "sensors", "disk"])
    cfg.setdefault("full", None)                # None = the whole collector fleet
    cfg.setdefault("fast_seconds", 5)
    cfg.setdefault("full_seconds", 60)
    cfg.setdefault("narrate", False)
    cfg.setdefault("url", "http://127.0.0.1:8081/watchtower")
    # env overrides (env always wins over the file)
    cfg["url"] = os.environ.get("WATCHTOWER_SHIP_URL", cfg["url"])
    cfg["host"] = os.environ.get("WATCHTOWER_HOST", cfg["host"])
    if "--narrate" in sys.argv:
        cfg["narrate"] = True
    return cfg


def narrate(snap):
    try:
        import schema, infer
        bundle = narrate.bundle = getattr(narrate, "bundle", None) or infer.load()
        return infer.generate_report(bundle, schema.serialize_metrics(snap))
    except Exception as e:
        return f"(narrator unavailable on agent: {e})"


def post(url, token, payload):
    req = urllib.request.Request(
        url, json.dumps(payload).encode(),
        {"Content-Type": "application/json", "X-Watchtower-Token": token})
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()


def main():
    cfg = load_config()
    token = os.environ.get("WATCHTOWER_TOKEN", "")
    print(f"shipping {cfg['host']} -> {cfg['url']} "
          f"(fast {cfg['fast_seconds']}s / full {cfg['full_seconds']}s"
          + (", narrated" if cfg["narrate"] else "") + ")")
    last_full = 0.0
    while True:
        t0 = time.time()
        partial = t0 - last_full < cfg["full_seconds"]
        snap = sysdiag.snapshot(only=cfg["fast"]) if partial else sysdiag.snapshot(only=cfg["full"])
        if not partial:
            last_full = t0
            if cfg["narrate"]:
                snap["_report"] = narrate(snap)
        try:
            post(cfg["url"], token, {"host": cfg["host"], "label": cfg["label"],
                                     "tags": cfg["tags"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "partial": partial, "snap": snap})
        except Exception as e:
            print("ship failed (will retry next tick):", e)   # NiFi/GUI down -> drop this
        #                                                       tick; NiFi buffers once it's back
        time.sleep(max(0.5, cfg["fast_seconds"] - (time.time() - t0)))


if __name__ == "__main__":
    main()
```

### `discover.py`

```python
# discover.py — scan the buses (USB/PCI via PnP, plus COM ports), map what's found to
# the collector that should cover it, and report coverage. `--spawn` writes a stub
# collector for any recognized device that has none (never overwrites). New stubs are
# picked up automatically by sysdiag.py's snapshot() glob — that's the whole loop:
#   plug it in -> discover sees it -> spawn stub -> fill stub -> it's in every snapshot.
import json, re, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).parent
COLLECTORS = HERE / "collectors"
sys.path.insert(0, str(COLLECTORS))
from _sdr_common import KNOWN as SDR_SIGS   # single source of truth for SDR signatures

# (VID, PID-or-None) -> (collector, label). PID None = any product from that vendor.
DEVICE_MAP = {sig: ("sdr", label) for sig, label in SDR_SIGS.items()}
DEVICE_MAP.update({
    ("1E71", None): ("sensors", "NZXT AIO (liquid temp: LHM or liquidctl)"),
    ("1B1C", None): ("lights",  "Corsair RGB (via OpenRGB SDK)"),
})

STUB = '''# collectors/{name}.py — AUTO-SPAWNED by discover.py for: {label}
# This device was seen on the bus with no collector covering it. Contract:
# print ONE json object namespaced under "{name}"; absent hardware -> {{"present": false}};
# hardware problems are values (rules.py judges them), exceptions only for real failures.
import json
print(json.dumps({{"{name}": {{"present": True, "stub": True,
                             "matched": "{label}",
                             "note": "auto-spawned stub - fill with real metrics"}}}}))
'''


def scan_pnp():
    ps = (r"Get-PnpDevice -PresentOnly -EA SilentlyContinue | "
          r"Select-Object Class,FriendlyName,InstanceId,Status | ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    devs = json.loads(out) if out else []
    return devs if isinstance(devs, list) else [devs]


def com_ports():
    ps = (r"(Get-ItemProperty 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM' -EA SilentlyContinue)."
          r"PSObject.Properties | Where-Object {$_.Name -notlike 'PS*'} | "
          r"ForEach-Object {$_.Value}")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=15).stdout
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def matches(devs):
    seen = {}
    for d in devs:
        m = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", d.get("InstanceId") or "", re.I)
        if not m:
            continue
        vid, pid = m.group(1).upper(), m.group(2).upper()
        hit = DEVICE_MAP.get((vid, pid)) or DEVICE_MAP.get((vid, None))
        if hit:
            seen.setdefault(hit, []).append(d.get("FriendlyName") or f"{vid}:{pid}")
    return seen


def main(spawn=False):
    devs = scan_pnp()
    hits = matches(devs)
    bad = [d for d in devs if (d.get("Status") or "OK") not in ("OK", "Unknown")]

    print(f"scanned {len(devs)} present PnP devices")
    for (collector, label), names in sorted(hits.items()):
        path = COLLECTORS / f"{collector}.py"
        state = "covered" if path.exists() else "NO COLLECTOR"
        print(f"  [{state:12}] {label} -> collectors/{collector}.py ({len(names)}x: {names[0]})")
        if spawn and not path.exists():
            path.write_text(STUB.format(name=collector, label=label), encoding="utf-8")
            print(f"               spawned {path.name} — fill it in, next snapshot runs it")
    for port in com_ports():
        print(f"  [candidate   ] serial port {port} — instruments here need a bespoke collector")
    for d in bad:
        print(f"  [problem     ] {d.get('FriendlyName')} status={d.get('Status')}")
    if not hits:
        print("  no mapped devices found (edit DEVICE_MAP / _sdr_common.KNOWN to teach it more)")


if __name__ == "__main__":
    main(spawn="--spawn" in sys.argv)
```

### `brain.py`

```python
### brain.py — the chatbot brain. Qwen2.5-32B via Ollama, grounded in the live system state from context.py. READ-ONLY: the model is told it cannot act, and nothing it returns is ever executed — its output is text shown to a human. ###

import json, urllib.request, urllib.error
import context

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:32b"            # Q4_K_M by default; fits the <GPU>'s 32GB VRAM

SYSTEM = """You are a hands-on hardware-diagnostics and troubleshooting expert for THIS
specific Windows 11 PC. You answer questions about its health and tell the user EXACTLY what
to do — as concrete, copy-pasteable steps.

How to answer — ALWAYS:
- Give numbered, step-by-step instructions. Assume the user copies and runs each step.
- For EVERY command state all four: (1) the shell — PowerShell; (2) the exact command in a code
  block; (3) the folder to run it from — give the literal `cd` command when it matters; (4)
  whether it needs an ELEVATED (Administrator) shell. If it does, say so first and tell them to
  open Windows Terminal / PowerShell "as Administrator" before that step.
- End with: what a successful result looks like, and the one thing to check if it fails.
- Prefer built-in Windows/PowerShell commands and the user's own `sysdiag` tool. Do NOT invent
  commands, flags, or file paths. If you're unsure a command exists or is safe, say so instead of
  guessing.
- BEFORE any destructive or risky step (deleting files, editing the registry, killing processes,
  anything elevated), put a one-line warning so the user reads it before running.

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


def ask(message, history, host=None):
    """Gradio ChatInterface fn (type='messages'): history is [{role,content}, ...].
    host (from the GUI's host selector as an additional_input) picks which machine to answer
    about; None (e.g. CLI chat.py) falls back to the sampler's focused/only host."""
    user_text = _text(message)
    msgs = [{"role": "system", "content": SYSTEM.format(ctx=context.build(user_text, host))}]
    msgs += [{"role": m["role"], "content": _text(m.get("content"))} for m in (history or [])]
    msgs.append({"role": "user", "content": user_text})
    body = json.dumps({"model": MODEL, "messages": msgs, "stream": False,
                       "keep_alive": "30m",  # stay resident between messages; reload only after long idle
                       "options": {"temperature": 0.3, "num_ctx": 32768}}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:  # 300s survives a 19GB cold load
            return json.loads(r.read())["message"]["content"]
    except urllib.error.HTTPError as e:  # show Ollama's own error, not a generic "can't reach"
        return f"(Ollama returned HTTP {e.code}: {e.read().decode(errors='replace')[:300]})"
    except Exception as e:
        return f"(couldn't reach Ollama at {OLLAMA}: {e}. Is `ollama` running? Try `ollama ps`.)"


def demo():  # the one runnable check: a grounded answer comes back (needs Ollama up)
    # the bug this guards: list-shaped content must flatten to a string, not 400 Ollama
    assert _text([{"type": "text", "text": "a"}, {"text": "b"}]) == "ab"
    assert _text("hi") == "hi" and _text(None) == ""
    reply = ask("Is anything wrong right now? One sentence.", [])
    assert isinstance(reply, str) and reply.strip(), "no reply from the brain"
    print("brain ok:", reply[:160])


if __name__ == "__main__":
    demo()
```

### `system_facts.md` (edit for YOUR machine)

Static facts the chat reads every message. Replace with your CPU/GPU model, normal temps, and what you care about.

```text
# This machine

- CPU: <your CPU> (cores/threads, TjMax). Note what temps are normal under load.
- GPU: <your GPU>, <VRAM>. Note the edge temp limit and expected load temps.
- RAM: <size/speed>.
- Storage: <OS drive>; other drives.
- Role: <what this box does> — runs Ollama, maybe Docker, a homelab.
- What I care about: failing components, thermal throttling, hardware errors, disks filling, a fan stalling.
```

### `ship.config.example.json`

Copy to `ship.config.json` on each monitored machine (gitignored).

```json
{
  "_comment": "Copy to ship.config.json on each MONITORED machine and edit. Env vars override any key here. This is where you set the reporter's identity and shape the shipped JSON.",

  "host": "lab-pc-01",
  "label": "Lab PC — rack 2, GPU node",
  "tags": { "location": "basement", "role": "gpu-node", "owner": "ops" },

  "fast": ["cpu", "gpu", "mem", "sensors", "disk"],
  "full": null,

  "fast_seconds": 5,
  "full_seconds": 60,

  "narrate": false,

  "url": "http://nifi-or-gui-host:8081/watchtower"
}
```

### `ssh.config.example.json`

Copy to `ssh.config.json` where the ssh collector runs (gitignored).

```json
{
  "_comment": "Collector: SSH into remote Linux VMs and scrape read-only checks. Copy to ssh.config.json (gitignored). KEY-BASED AUTH ONLY — set up an SSH key to each VM first (ssh-copy-id); passwords are disabled. A new VM must be in known_hosts, or set accept_new:true for trust-on-first-use. Reading a file = a check whose cmd is `cat`/`grep /path`.",

  "connect_timeout": 6,

  "targets": [
    {
      "name": "db-vm",
      "ssh": "monitor@10.0.0.5",
      "port": 22,
      "key": "~/.ssh/id_ed25519",
      "accept_new": false,
      "jump": "monitor@bastion.example",
      "checks": {
        "disk_root_pct":  { "cmd": "df --output=pcent / | tail -1 | tr -dc 0-9", "warn": 85, "crit": 95, "unit": "%" },
        "load1":          { "cmd": "cut -d' ' -f1 /proc/loadavg", "warn": 8, "crit": 16 },
        "mem_used_pct":   { "cmd": "free | awk '/Mem:/ {printf \"%d\", $3/$2*100}'", "warn": 90, "crit": 97, "unit": "%" },
        "postgres":       "systemctl is-active postgresql",
        "cert_days_left": { "cmd": "echo $(( ( $(date -d \"$(openssl x509 -enddate -noout -in /etc/ssl/certs/site.pem | cut -d= -f2)\" +%s) - $(date +%s) ) / 86400 ))", "warn": 30, "crit": 7, "unit": "d" },
        "app_debug_on":   "grep -c '^DEBUG=true' /etc/myapp/config.env || true",
        "last_backup_age_h": { "cmd": "echo $(( ( $(date +%s) - $(stat -c %Y /var/backups/db.sql.gz) ) / 3600 ))", "warn": 26, "crit": 50, "unit": "h" }
      }
    },
    {
      "name": "web-vm",
      "ssh": "monitor@10.0.0.6",
      "checks": {
        "nginx":         "systemctl is-active nginx",
        "http_health":   "curl -s --max-time 4 -o /dev/null -w '%{http_code}' http://localhost/health",
        "open_fds_pct":  { "cmd": "awk '{print int($1/$3*100)}' /proc/sys/fs/file-nr 2>/dev/null || echo 0", "warn": 80, "crit": 95, "unit": "%" }
      }
    }
  ]
}
```

### `.gitignore`

```text
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Trained model checkpoint + runtime data (regenerable; large or machine-specific)
ckpt.pt
*.pt
*.safetensors
history.db
history.log
notes.db
# RAG embedding cache — regenerate with `python rag.py --build`
# (a trailing comment on the pattern line breaks the match: gitignore comments must be whole-line)
rag_index.db
*.db-journal

# Large generated/scraped RAG corpora (regenerable; see docs/RECREATE-*.md §12).
# rag.py still indexes these locally via its *.md glob — they're just kept out of git.
powershell-docs-merged.md
arch-wiki-merged.md
linux_wiki.md
windows-commands.md

# Third-party copyrighted reference docs — indexed locally by rag.py, kept out of the public repo.
MAG_Z790_TOMAHAWK_MAX_WIFI_User_Guide.md
sysinternals.md
WindowsHardwareErrorArchitecture.md
ansible-core-narrative-docs.md
kernel-maintainer-handbook.md
nvidia-smi.md

# Local agent / security-sweep artifacts (never commit)
.claude/

# Secrets / env
.env
.env.*

# Per-machine agent configs (real ones carry hostnames/keys/topology; keep the *.example.json)
ship.config.json
ssh.config.json

# OS cruft
Thumbs.db
.DS_Store
```

## 6. Build it — step by step (with expected output)

### 6.1 Virtual env + dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install gradio pandas sqlite-vec
# sqlite-vec powers the optional RAG (§12); everything else the app uses is stdlib.
# optional deep-sensor deps: pip install liquidctl openrgb-python
```
Confirm torch sees your GPU:
```powershell
python -c "import torch,gradio,pandas; print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
```
> `cuda True` means the GPU is visible. `False` still runs (the GPT trains on CPU in minutes; the
> 32B Ollama model wants a GPU to be usable).

### 6.2 Sanity-check the pure-logic modules
```powershell
python schema.py
python rules.py
python live.py
python collectors/docker.py --test
```
Expected: `schema ok`, `rules ok`, `live ok — ...`, `docker parsers ok`.

### 6.3 Generate the corpus, train, test the GPT
```powershell
python data.py 8000        # -> wrote corpus.txt: 8000 docs (deterministic, seed 1337)
python train.py            # -> ~3 min on a CUDA GPU (bf16) / ~20-30 min CPU; val loss ~0.19;
#                             writes ckpt.pt (~47 MB) + vocab.json
python infer.py --demo     # -> MODEL OUTPUT should read like the GROUND TRUTH
```
> `corpus.txt`, `vocab.json`, and `ckpt.pt` are **generated artifacts** — regenerable and
> git-ignored. `data.py` is deterministic, so the corpus reproduces byte-for-byte. Retrain
> whenever you change `schema.serialize_metrics` / `data.render_report` / the corpus size.

### 6.4 Run the live collectors
With LibreHardwareMonitor running:
```powershell
python collectors\gpu.py
python collectors\sensors.py
python sysdiag.py
```
> `tpm` blank and unelevated `storage` wear/temp null are expected — run PowerShell **as Administrator** for full detail.

### 6.5 Full live snapshot as JSON
```powershell
python sysdiag.py diag --json
```
A big pretty-printed JSON object with every collector's namespace — exactly what `context.py`
feeds the chat model, and what `ship.py` streams in remote mode.

### 6.6 Discover devices (optional)
```powershell
python sysdiag.py discover           # list known devices -> collector coverage
python sysdiag.py discover --spawn   # stub a collector for a recognized, uncovered device
```

---

## 7. Connect Ollama (the chat brain)

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
```powershell
python chat.py
```
Banner, then a prompt. Ask "Is my GPU temp normal?" — grounded answer. `exit` frees VRAM.

### Web dashboard
```powershell
$env:PYTHONIOENCODING = "utf-8"; python app.py
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

## 9. Remote monitoring, multi-host & NiFi

Collectors run on the **monitored** machine; the dashboard/rules/chat run on the **monitoring**
machine; the tiny NanoGPT narrator is portable. The agent side is stdlib-only — copy
`collectors/`, `sysdiag.py`, `ship.py` (no pip installs).

```powershell
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

## 10. Schedule history logging (the History graph's data)

`history.py` appends one snapshot to `history.db` per run. Schedule it every ~15 min:

```powershell
$py  = "C:\Users\<you>\sysdiag\.venv\Scripts\python.exe"
$arg = "C:\Users\<you>\sysdiag\history.py"
$act = New-ScheduledTaskAction -Execute $py -Argument $arg -WorkingDirectory "C:\Users\<you>\sysdiag"
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

## 12. Add a local RAG pipeline (semantic doc retrieval)

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

