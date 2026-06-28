# trends.py — read history.db and return time-series DataFrames for the UI graphs.
# history.db is filled by the Task Scheduler logger (history.py); this only reads it.
import json, sqlite3, pathlib, datetime
import pandas as pd

DB = pathlib.Path(__file__).parent / "history.db"

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


def series(metric, runs_label="Last 25 runs"):
    path = METRICS.get(metric)
    if path is None or not DB.exists():
        return pd.DataFrame({"time": [], "value": [], "when": []})
    limit = RUNS.get(runs_label)
    query = "SELECT ts, json FROM snapshots ORDER BY ts DESC"
    if limit:
        query += f" LIMIT {int(limit)}"   # int() guards the f-string against injection
    rows = sqlite3.connect(DB).execute(query).fetchall()
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
