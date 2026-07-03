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
