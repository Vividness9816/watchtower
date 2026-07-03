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
