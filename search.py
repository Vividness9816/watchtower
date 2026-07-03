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
    where, params = [], []
    if host is not None:
        where.append("host = ?"); params.append(host)
    if since is not None:
        where.append("ts >= ?"); params.append(since)
    if until is not None:
        where.append("ts <= ?"); params.append(until)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    comp = component.lower() if component else None
    out = []
    with sqlite3.connect(DB) as con:
        try:
            rows = con.execute(f"SELECT ts, host, json FROM snapshots{clause} ORDER BY ts DESC",
                               params).fetchall()
        except sqlite3.OperationalError:
            # pre-host DB (no host column): re-query without host filtering, tag rows as unknown
            rows = con.execute("SELECT ts, json FROM snapshots ORDER BY ts DESC").fetchall()
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
