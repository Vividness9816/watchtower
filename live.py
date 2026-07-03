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
