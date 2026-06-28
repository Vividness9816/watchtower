# history.py — append one snapshot to a SQLite history DB. Run on a timer (Task Scheduler).
# Same data as `sysdiag --json`, stored as one row: timestamp + the full snapshot JSON.
import sqlite3, json, time, pathlib
import sysdiag

DB = pathlib.Path(__file__).parent / "history.db"   # absolute, so CWD doesn't matter

def main():
    snap = sysdiag.snapshot()                        # runs the collectors (local sensors)
    with sqlite3.connect(DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS snapshots (ts TEXT, json TEXT)")
        con.execute("INSERT INTO snapshots VALUES (?, ?)",
                    (time.strftime("%Y-%m-%dT%H:%M:%S"), json.dumps(snap)))
    print("logged", time.strftime("%H:%M:%S"))

if __name__ == "__main__":
    main()