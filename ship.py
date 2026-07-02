# ship.py — run on the MONITORED machine: stream snapshots as JSON to the monitoring
# side, either straight to Watchtower's /ingest or through Apache NiFi (ListenHTTP ->
# InvokeHTTP). Stdlib only — the agent needs collectors/ + sysdiag.py + this file,
# no pip installs. Two-tier cadence: FAST collectors every fast_seconds ({"partial":true}),
# the full fleet every full_seconds.
#
# CUSTOMIZE THE SHIPPED JSON via ship.config.json (see ship.config.example.json):
#   host        identity of THIS machine — how the monitoring side names/selects it
#   label,tags  free-form display label + key/value metadata merged into every payload
#   fast,full   which collectors go in each tier (full: null = the whole fleet)
#   *_seconds   cadence;  narrate: attach the local NanoGPT report to full snapshots
#   url         where to POST
# The identity/destination keys are env-overridable (env wins) so ONE shared config can serve
# many machines by varying just these two on the command line — host via WATCHTOWER_HOST, url
# via WATCHTOWER_SHIP_URL. Other keys (label/tags/fast/full/cadence/narrate) come from the file
# (or --narrate). Also honoured: WATCHTOWER_TOKEN (secret), WATCHTOWER_SHIP_CONFIG (config path).
#
# `python ship.py --narrate` (or "narrate": true) runs the local NanoGPT narrator on each
# FULL snapshot and ships its report as snap["_report"] (needs torch + ckpt.pt here; without
# them the flag degrades to a note and keeps shipping raw metrics).
import json, os, socket, sys, time, urllib.request
import sysdiag

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.environ.get("WATCHTOWER_SHIP_CONFIG", os.path.join(HERE, "ship.config.json"))
    cfg = {}
    try:
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            cfg = {k: v for k, v in loaded.items() if not k.startswith("_")}
        else:
            print("ship.config.json ignored (not a JSON object)")   # a list/number/string
    except FileNotFoundError:
        pass                                    # config is optional; env + defaults suffice
    except (json.JSONDecodeError, OSError) as e:
        print(f"ship.config.json ignored ({e})")
    cfg.setdefault("host", socket.gethostname())
    cfg.setdefault("label", "")
    cfg.setdefault("tags", {})
    cfg.setdefault("fast", ["cpu", "gpu", "mem", "sensors", "disk"])
    cfg.setdefault("full", None)                # None = the whole collector fleet
    cfg.setdefault("fast_seconds", 5)
    cfg.setdefault("full_seconds", 60)
    cfg.setdefault("narrate", False)
    cfg.setdefault("url", "http://127.0.0.1:8081/watchtower")
    # env overrides (env always wins over the file)
    cfg["url"] = os.environ.get("WATCHTOWER_SHIP_URL", cfg["url"])
    cfg["host"] = os.environ.get("WATCHTOWER_HOST", cfg["host"])
    if "--narrate" in sys.argv:
        cfg["narrate"] = True
    return cfg


def narrate(snap):
    try:
        import schema, infer
        bundle = narrate.bundle = getattr(narrate, "bundle", None) or infer.load()
        return infer.generate_report(bundle, schema.serialize_metrics(snap))
    except Exception as e:
        return f"(narrator unavailable on agent: {e})"


def post(url, token, payload):
    req = urllib.request.Request(
        url, json.dumps(payload).encode(),
        {"Content-Type": "application/json", "X-Watchtower-Token": token})
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()


def main():
    cfg = load_config()
    token = os.environ.get("WATCHTOWER_TOKEN", "")
    print(f"shipping {cfg['host']} -> {cfg['url']} "
          f"(fast {cfg['fast_seconds']}s / full {cfg['full_seconds']}s"
          + (", narrated" if cfg["narrate"] else "") + ")")
    last_full = 0.0
    while True:
        t0 = time.time()
        partial = t0 - last_full < cfg["full_seconds"]
        snap = sysdiag.snapshot(only=cfg["fast"]) if partial else sysdiag.snapshot(only=cfg["full"])
        if not partial:
            last_full = t0
            if cfg["narrate"]:
                snap["_report"] = narrate(snap)
        try:
            post(cfg["url"], token, {"host": cfg["host"], "label": cfg["label"],
                                     "tags": cfg["tags"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "partial": partial, "snap": snap})
        except Exception as e:
            print("ship failed (will retry next tick):", e)   # NiFi/GUI down -> drop this
        #                                                       tick; NiFi buffers once it's back
        time.sleep(max(0.5, cfg["fast_seconds"] - (time.time() - t0)))


if __name__ == "__main__":
    main()
