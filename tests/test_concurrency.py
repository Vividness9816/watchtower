# tests/test_concurrency.py — stress the two write paths that take concurrent input in
# remote/multi-user mode: live._record (per-host rings under _lock, hit by the ingest
# ThreadingHTTPServer) and notes.add_note (SQLite, hit by multiple dashboard users).
# Asserts: no exception in any thread, exact final counts, no cross-host bleed.
import os, pathlib, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["WATCHTOWER_NOTES_DB"] = str(pathlib.Path(tempfile.mkdtemp()) / "stress.db")
import live, notes  # noqa: E402

WRITERS, ITERS, HOSTS = 16, 200, 8       # 3200 records, 400/host — under KEEP so counts are exact


def test_live_record_stress():
    live._hosts.clear()
    errors = []

    def writer(w):
        try:
            for i in range(ITERS):
                live._record({"cpu": {"load": w}, "sensors": {"cpu_temp": 40 + w},
                              "_errors": ["synthetic"] if i % 7 == 0 else []},
                             merge=(i % 3 == 0), host=f"host-{(w + i) % HOSTS}")
        except Exception as e:                          # pragma: no cover - the failure signal
            errors.append(e)

    def reader():
        try:
            for _ in range(200):
                live.hosts()
                live.get_latest("host-0")
                live.frame(["CPU load (%)", "CPU temp (C)"], "5 min", host="host-1")
                live.deltas(1, host="host-2")
        except Exception as e:                          # pragma: no cover
            errors.append(e)

    ts = [threading.Thread(target=writer, args=(w,)) for w in range(WRITERS)]
    ts += [threading.Thread(target=reader) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(60)
    assert not any(t.is_alive() for t in ts), "a thread hung (deadlock?)"
    assert not errors, errors[:3]
    assert sorted(live._hosts) == [f"host-{i}" for i in range(HOSTS)], sorted(live._hosts)
    total = sum(len(st["buf"]) for st in live._hosts.values())
    assert total == WRITERS * ITERS, f"ring lost/duplicated records: {total} != {WRITERS * ITERS}"
    for h, st in live._hosts.items():
        assert st["snap"]["_host"] == h, f"cross-host bleed into {h}"
        assert len(st["buf"]) == WRITERS * ITERS // HOSTS, (h, len(st["buf"]))
    live._hosts.clear()


def test_notes_add_stress():
    n_writers, per = 12, 40
    errors = []

    def writer(u):
        try:
            for i in range(per):
                notes.add_note(f"user{u}", f"note {u}-{i}", host=f"h{u}")
        except Exception as e:                          # pragma: no cover
            errors.append(e)

    def reader():
        try:
            for _ in range(30):
                notes.list_notes(limit=50)
        except Exception as e:                          # pragma: no cover
            errors.append(e)

    ts = [threading.Thread(target=writer, args=(u,)) for u in range(n_writers)]
    ts += [threading.Thread(target=reader) for _ in range(3)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(120)
    assert not any(t.is_alive() for t in ts), "a thread hung on the notes DB"
    assert not errors, errors[:3]
    got = notes.list_notes(limit=n_writers * per + 10)
    assert len(got) == n_writers * per, f"notes lost/duplicated: {len(got)} != {n_writers * per}"


if __name__ == "__main__":
    for fn in (test_live_record_stress, test_notes_add_stress):
        fn()
        print(f"  ok  {fn.__name__}")
    print("concurrency ok")
