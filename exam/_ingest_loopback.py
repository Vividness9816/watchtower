# _ingest_loopback.py — exam helper: prove the remote-ingest trust boundary end-to-end on
# 127.0.0.1. Run in a fresh interpreter (live.py module state must be clean) with
# WATCHTOWER_TOKEN=exam-secret WATCHTOWER_REMOTE=1. Prints "ingest ok" iff every check holds.
import json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import live  # noqa: E402

TOKEN = os.environ["WATCHTOWER_TOKEN"]
BIND = "127.0.0.1:7899"
URL = f"http://{BIND}/ingest"


def post(payload, token=TOKEN, raw=None):
    body = raw if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json",
                                             "X-Watchtower-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    live.start_receiver(bind=BIND)
    time.sleep(0.3)
    full = {"host": "exam-agent", "label": "Exam", "tags": {"role": "test"}, "partial": False,
            "snap": {"cpu": {"load": 11}, "sensors": {"cpu_temp": 41}, "net": {"ping_ms": 9}}}
    assert post(full) == 200, "good full payload must 200"
    snap, age, _ = live.get_latest("exam-agent")
    assert snap.get("cpu", {}).get("load") == 11 and snap.get("_host") == "exam-agent", snap
    assert snap.get("_label") == "Exam", "label must be stamped in"
    partial = {"host": "exam-agent", "partial": True,
               "snap": {"cpu": {"load": 77}, "sensors": {"cpu_temp": 55}}}
    assert post(partial) == 200
    snap, _, _ = live.get_latest("exam-agent")
    assert snap["cpu"]["load"] == 77, "partial must update fast keys"
    assert snap.get("net", {}).get("ping_ms") == 9, "partial must PRESERVE full-tier keys"
    assert post(full, token="wrong-token") == 403, "bad token must 403"
    assert post(None, raw=b"{not json") == 400, "bad JSON must 400"
    assert post(None, raw=b"x" * 2_000_001) == 413, "oversized body must 413"
    assert post({"host": "exam-agent", "partial": False, "snap": "pwn"}) == 400, "non-dict snap must 400"
    assert "exam-agent" in live.hosts()
    # hostile _errors type: must answer with a clean HTTP status (200 after sanitize, or 400),
    # never a connection reset, and must not corrupt the host's ring for later payloads
    code = post({"host": "exam-agent", "partial": True, "snap": {"_errors": "oops-string"}})
    assert code in (200, 400), f"_errors-as-string must degrade cleanly, got {code}"
    assert post({"host": "exam-agent", "partial": True,
                 "snap": {"cpu": {"load": 33}, "sensors": {"cpu_temp": 44}}}) == 200, \
        "ring corrupted by hostile _errors payload"
    snap, age, _ = live.get_latest("exam-agent")
    assert snap["cpu"]["load"] == 33 and age < 5, "state/stamp corrupted by hostile _errors"
    # a brand-new host whose FIRST payload is partial must still create a working ring
    assert post({"host": "exam-fresh", "partial": True,
                 "snap": {"cpu": {"load": 5}, "sensors": {"cpu_temp": 40}}}) == 200
    fresh, _, _ = live.get_latest("exam-fresh")
    assert fresh.get("cpu", {}).get("load") == 5, "partial-first payload lost"
    print("ingest ok")


if __name__ == "__main__":
    main()
