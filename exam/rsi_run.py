# rsi_run.py — RSI loop orchestrator (NOT part of the frozen exam; it only calls it).
# Runs the exam dimensions a given change can affect, inherits the deterministic rest from the
# previous run, recomputes the composite with the FROZEN weights, and appends to the scoreboard.
# The exam itself (run_exam.py + data) stays byte-frozen; this just avoids re-burning 5 min of GPU
# on S3/S5 when a change couldn't have touched them. Do a full run (--dims all) to certify.
#
#   python exam/rsi_run.py --run 1 --dims s1,s2          # run S1+S2, inherit s3..s7 from run 0
#   python exam/rsi_run.py --run 9 --dims all            # certify: run everything, inherit nothing
import argparse, json, pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent
RES = HERE / "results"
PY = sys.executable
W = {"s1": 0.15, "s2": 0.15, "s3": 0.20, "s4": 0.10, "s5": 0.15, "s6": 0.10, "s7": 0.15}
ALL = list(W)


def latest_merged(before_run):
    """Most recent run-<k>.merged.json (or run-0.json) with k < before_run, for inheritance."""
    best, best_k = None, -1
    for p in RES.glob("run-*.json"):
        stem = p.stem.replace(".merged", "")
        try:
            k = int(stem.split("-")[1])
        except (IndexError, ValueError):
            continue
        if k < before_run and k > best_k:
            best, best_k = p, k
    return json.loads(best.read_text(encoding="utf-8")) if best else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--dims", required=True, help="comma list e.g. s1,s2  OR  all")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    dims = ALL if args.dims.strip() == "all" else [d.strip() for d in args.dims.split(",") if d.strip()]

    prev = latest_merged(args.run)
    prev_scores = (prev or {}).get("scores", {})
    if dims != ALL and prev is None:
        print("no prior run to inherit from — use --dims all for the first run", file=sys.stderr)
        sys.exit(2)

    t0 = time.time()
    # run only the requested dims through the frozen exam; it writes results/run-<N>.json
    r = subprocess.run([PY, "exam/run_exam.py", "--run", str(args.run), "--only", ",".join(dims)],
                       cwd=str(REPO))
    fresh = json.loads((RES / f"run-{args.run}.json").read_text(encoding="utf-8"))
    scores = dict(prev_scores)
    for d in dims:
        scores[d] = fresh["scores"].get(d)
    inherited = [d for d in ALL if d not in dims]
    missing = [d for d in ALL if scores.get(d) is None]
    composite = round(sum(W[d] * scores[d] for d in ALL), 4) if not missing else None

    merged = {"run": args.run, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "dims_run": dims, "dims_inherited": inherited,
              "frozen_ok": fresh.get("frozen_ok"),
              "scores": {d: (None if scores.get(d) is None else round(scores[d], 4)) for d in ALL},
              "composite": composite, "note": args.note,
              "seconds": round(time.time() - t0, 1)}
    (RES / f"run-{args.run}.merged.json").write_text(json.dumps(merged, indent=1), encoding="utf-8")

    prev_comp = (prev or {}).get("composite")
    delta = None if (composite is None or prev_comp is None) else round(composite - prev_comp, 4)
    print(json.dumps({"run": args.run, "scores": merged["scores"], "composite": composite,
                      "prev": prev_comp, "delta": delta, "frozen_ok": merged["frozen_ok"],
                      "inherited": inherited}, indent=1))


if __name__ == "__main__":
    main()
