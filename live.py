# live.py — background sampler feeding the GUI's live graphs and the chat brain.
# Two tiers: FAST collectors every FAST_S seconds, the FULL fleet every FULL_S — so the
# dashboard stays live without spawning 19 processes (10 of them PowerShell) every tick.
# In-memory ring buffer only (~1h); long-term history stays with history.py/Task Scheduler.
import threading, time, collections
import pandas as pd
import sysdiag

FAST_S, FULL_S = 5, 60
FAST = ["cpu", "gpu", "mem", "sensors", "disk"]     # cheap collectors, safe at 5s cadence
KEEP = 3600 // FAST_S                               # ~1h of points

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
    "Ping (ms)":        ("net", "ping_ms"),
    "DNS (ms)":         ("net", "dns_ms"),
}

_lock = threading.Lock()
_snap: dict = {}
_stamp = 0.0
_buf = collections.deque(maxlen=KEEP)               # (epoch, {label: value})
_thread = None


def _dig(snap, path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _record(fresh, merge):
    global _snap, _stamp
    with _lock:
        _snap = {**_snap, **fresh} if merge else fresh
        _stamp = time.time()
        _buf.append((_stamp, {lbl: _dig(_snap, p) for lbl, p in METRICS.items()}))


def _loop():
    last_full = time.time()                          # start() already took the first full
    while True:
        t0 = time.time()
        if t0 - last_full >= FULL_S:
            _record(sysdiag.snapshot(), merge=False)
            last_full = t0
        else:
            _record(sysdiag.snapshot(only=FAST), merge=True)
        time.sleep(max(0.5, FAST_S - (time.time() - t0)))


def start():
    """Idempotent. Takes one synchronous FULL snapshot so the first paint has data."""
    global _thread
    if _thread and _thread.is_alive():
        return
    _record(sysdiag.snapshot(), merge=False)
    _thread = threading.Thread(target=_loop, daemon=True, name="live-sampler")
    _thread.start()


def get_latest():
    """-> (snapshot dict, age_seconds). Empty dict + inf if the sampler never ran."""
    with _lock:
        return dict(_snap), (time.time() - _stamp if _stamp else float("inf"))


SPANS = {"5 min": 5, "15 min": 15, "60 min": 60}


def frame(labels, span="15 min"):
    """Long-form DataFrame (time, value, series) for the selected metrics — LinePlot food."""
    cutoff = time.time() - SPANS.get(span, 15) * 60
    labels = [l for l in (labels or []) if l in METRICS]
    with _lock:
        rows = [(ts, vals) for ts, vals in _buf if ts >= cutoff]
    t, v, s = [], [], []
    for ts, vals in rows:
        for lbl in labels:
            if vals.get(lbl) is not None:
                t.append(ts)
                v.append(vals[lbl])
                s.append(lbl)
    return pd.DataFrame({"time": pd.to_datetime(t, unit="s"), "value": v, "series": s})


def deltas(minutes=10):
    """Compact per-metric trend text for the LLM: 'CPU temp (C): 45 -> 52 (min 44, max 53)'."""
    cutoff = time.time() - minutes * 60
    with _lock:
        rows = [vals for ts, vals in _buf if ts >= cutoff]
    lines = []
    for lbl in METRICS:
        seq = [r[lbl] for r in rows if r.get(lbl) is not None]
        if len(seq) >= 2 and (min(seq) != max(seq) or seq[0] != seq[-1]):
            lines.append(f"{lbl}: {seq[0]} -> {seq[-1]} (min {min(seq)}, max {max(seq)}, n={len(seq)})")
        elif seq:
            lines.append(f"{lbl}: steady at {seq[-1]} (n={len(seq)})")
    return "\n".join(lines)


def demo():  # the one runnable check: sampler produces rows and frame() shapes them
    start()
    time.sleep(FAST_S + 2)
    snap, age = get_latest()
    assert snap and age < FAST_S + 3, f"sampler not live (age {age})"
    df = frame(["CPU load (%)", "GPU temp (C)"], "5 min")
    assert list(df.columns) == ["time", "value", "series"] and len(df) >= 1, "frame broken"
    assert deltas(), "deltas empty"
    print(f"live ok — {len(df)} plot rows, snapshot age {age:.1f}s")


if __name__ == "__main__":
    demo()
