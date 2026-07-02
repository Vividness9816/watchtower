# ship.py — run on the MONITORED machine: stream snapshots as JSON to the monitoring
# side, either straight to Watchtower's /ingest or through Apache NiFi (ListenHTTP ->
# InvokeHTTP). Stdlib only — the agent box needs collectors/ + sysdiag.py + this file,
# no pip installs. Same two-tier cadence as live.py: FAST collectors every 5s
# ({"partial": true}), the full fleet every 60s.
#
#   WATCHTOWER_SHIP_URL   where to POST (NiFi ListenHTTP or Watchtower /ingest directly)
#   WATCHTOWER_TOKEN      shared secret; the receiver rejects anything without it
#   WATCHTOWER_HOST       optional hostname override in the payload
#
# `python ship.py --narrate` additionally runs the local NanoGPT narrator on each FULL
# snapshot and ships its report text as snap["_report"] (needs torch + ckpt.pt here;
# without them the flag degrades to a note and keeps shipping raw metrics).
import json, os, socket, sys, time, urllib.request
import sysdiag

URL = os.environ.get("WATCHTOWER_SHIP_URL", "http://127.0.0.1:8081/watchtower")
TOKEN = os.environ.get("WATCHTOWER_TOKEN", "")
HOST = os.environ.get("WATCHTOWER_HOST", socket.gethostname())
FAST_S, FULL_S = 5, 60
FAST = ["cpu", "gpu", "mem", "sensors", "disk"]


def narrate(snap):
    try:
        import schema, infer
        bundle = narrate.bundle = getattr(narrate, "bundle", None) or infer.load()
        return infer.generate_report(bundle, schema.serialize_metrics(snap))
    except Exception as e:
        return f"(narrator unavailable on agent: {e})"


def post(payload):
    req = urllib.request.Request(
        URL, json.dumps(payload).encode(),
        {"Content-Type": "application/json", "X-Watchtower-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()


def main(with_report=False):
    print(f"shipping {HOST} -> {URL} (fast {FAST_S}s / full {FULL_S}s"
          + (", narrated" if with_report else "") + ")")
    last_full = 0.0
    while True:
        t0 = time.time()
        partial = t0 - last_full < FULL_S
        snap = sysdiag.snapshot(only=FAST) if partial else sysdiag.snapshot()
        if not partial:
            last_full = t0
            if with_report:
                snap["_report"] = narrate(snap)
        try:
            post({"host": HOST, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "partial": partial, "snap": snap})
        except Exception as e:
            print("ship failed (will retry next tick):", e)   # NiFi/GUI down -> drop this
        #                                                       tick; NiFi buffers once it's
        #                                                       back up, so nothing else needed
        time.sleep(max(0.5, FAST_S - (time.time() - t0)))


if __name__ == "__main__":
    main(with_report="--narrate" in sys.argv)
