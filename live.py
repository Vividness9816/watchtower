# live.py — background sampler feeding the GUI's live graphs and the chat brain.
# Two tiers: FAST collectors every FAST_S seconds, the FULL fleet every FULL_S — so the
# dashboard stays live without spawning 19 processes (10 of them PowerShell) every tick.
# In-memory ring buffer only (~1h); long-term history stays with history.py/Task Scheduler.
#
# REMOTE mode (WATCHTOWER_REMOTE=1): instead of sampling THIS machine, run an HTTP
# receiver and let a monitored machine push snapshots in (ship.py -> NiFi -> /ingest).
# Same ring, same graphs, same chat context — only the data source changes.
import hmac, json, os, threading, time, collections
import pandas as pd
import sysdiag

REMOTE = os.environ.get("WATCHTOWER_REMOTE") == "1"
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
    "Disk C used (%)":  ("disk", "C"),
    "Ping (ms)":        ("net", "ping_ms"),
    "DNS (ms)":         ("net", "dns_ms"),
    "WHEA errors":      ("whea", "recent_errors"),
}
# labels backed by FAST-tier collectors get a fresh point every tick; the rest only when
# the full fleet runs — recording them per-tick would fake 12 duplicate samples per real one
FAST_LABELS = {lbl for lbl, path in METRICS.items() if path[0] in FAST}

_lock = threading.Lock()
_snap: dict = {}
_stamp = 0.0                                        # last record of ANY tier
_full_stamp = 0.0                                   # last FULL-fleet record
_errs = {"fast": [], "full": []}                    # per-tier, so a recovered tick clears its own
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
    global _snap, _stamp, _full_stamp
    errs = fresh.pop("_errors", [])
    with _lock:
        if merge:                                   # fast tier: authoritative for its own errors
            _errs["fast"] = errs
            _snap = {**_snap, **fresh}
            labels = FAST_LABELS
        else:                                       # full fleet: authoritative for everything
            _errs["fast"], _errs["full"] = [], errs
            _snap = fresh
            _full_stamp = time.time()
            labels = METRICS.keys()
        combined = _errs["fast"] + _errs["full"]
        _snap.pop("_errors", None)
        if combined:
            _snap["_errors"] = combined
        _stamp = time.time()
        _buf.append((_stamp, {lbl: _dig(_snap, METRICS[lbl]) for lbl in labels}))


def _loop():
    last_full = time.time()                          # start() already took the first full
    while True:
        t0 = time.time()
        try:
            if t0 - last_full >= FULL_S:
                _record(sysdiag.snapshot(), merge=False)
                last_full = t0
            else:
                _record(sysdiag.snapshot(only=FAST), merge=True)
        except Exception:
            pass    # a transient failure (or interpreter shutdown race) must not kill the
        #             sampler for the rest of the app's life; the next tick retries
        time.sleep(max(0.5, FAST_S - (time.time() - t0)))


def start():
    """Idempotent. Takes one synchronous FULL snapshot so the first paint has data."""
    global _thread
    if _thread and _thread.is_alive():
        return
    _record(sysdiag.snapshot(), merge=False)
    _thread = threading.Thread(target=_loop, daemon=True, name="live-sampler")
    _thread.start()


def start_receiver(bind=None, token=None):
    """REMOTE mode: accept snapshots pushed by ship.py (directly or via NiFi InvokeHTTP).
    POST /ingest, JSON {host, partial, snap}; X-Watchtower-Token header must match.
    Merge is per-collector (top-level keys replace wholesale), so a partial payload must
    carry COMPLETE collector objects for the collectors it includes — ship.py does."""
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
            if not hmac.compare_digest(self.headers.get("X-Watchtower-Token", ""), token):
                return self._reply(403)
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= 2_000_000:                       # a snapshot is ~50KB; cap abuse
                return self._reply(413)
            try:
                p = json.loads(self.rfile.read(n))
                snap = p["snap"]
                if not isinstance(snap, dict):
                    raise TypeError("snap must be an object")
            except Exception:
                return self._reply(400, b"bad payload")
            snap["_host"] = str(p.get("host", "?"))[:64]      # ponytail: ONE monitored host —
            _record(snap, merge=bool(p.get("partial")))       # last-writer-wins; per-host rings
            self._reply(200, b"ok")                           # when a second agent shows up

        def log_message(self, *_):                            # quiet: 12 req/min is not news
            pass

    srv = ThreadingHTTPServer((host, int(port)), Ingest)
    threading.Thread(target=srv.serve_forever, daemon=True, name="live-ingest").start()
    return srv


def get_latest():
    """-> (snapshot, fast_age_s, full_age_s). Empty dict + inf/inf if the sampler never ran."""
    now = time.time()
    with _lock:
        return (dict(_snap),
                now - _stamp if _stamp else float("inf"),
                now - _full_stamp if _full_stamp else float("inf"))


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
    snap, age, full_age = get_latest()
    assert snap and age < FAST_S + 3, f"sampler not live (age {age})"
    assert full_age < FULL_S + 30, f"no full pass (age {full_age})"
    df = frame(["CPU load (%)", "GPU temp (C)"], "5 min")
    assert list(df.columns) == ["time", "value", "series"] and len(df) >= 1, "frame broken"
    assert deltas(), "deltas empty"
    # per-tier recording: a fast tick must NOT re-record full-only labels like Ping (ms)
    with _lock:
        fast_rows = [vals for ts, vals in _buf if "Ping (ms)" not in vals]
    assert fast_rows, "fast ticks are re-recording full-tier labels"
    print(f"live ok — {len(df)} plot rows, fast age {age:.1f}s, full age {full_age:.1f}s")


if __name__ == "__main__":
    demo()
