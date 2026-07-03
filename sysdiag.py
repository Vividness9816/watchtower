import json, glob, subprocess, sys, pathlib, argparse
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).parent


def snapshot(only=None) -> dict:
    """only: None = all collectors, "name" = one, ["a","b"] = a subset (live.py fast tier).
    An empty list means zero collectors (returns {}), not the full fleet; unknown names in a
    list are reported once in _errors instead of spawning a doomed subprocess."""
    snap = {}
    if only is not None and not isinstance(only, str):
        want = [(n, HERE / "collectors" / f"{n}.py") for n in sorted(only)]
        files = [str(p) for n, p in want if p.exists()]
        for n, p in want:
            if not p.exists():
                snap.setdefault("_errors", []).append(f"{n}: unknown collector")
    else:
        pattern = str(HERE / "collectors" / (f"{only}.py" if only else "*.py"))
        files = sorted(glob.glob(pattern))
    files = [f for f in files
             if not pathlib.Path(f).name.startswith("_")]   # _*.py = shared libs, not collectors
    if not files:
        return snap

    def run_one(f):
        # -P keeps collectors/ off the child's sys.path so usb.py/power.py can't shadow pip pkgs
        return subprocess.run([sys.executable, "-P", f],
                              capture_output=True, text=True, timeout=25).stdout

    with ThreadPoolExecutor(max_workers=min(8, len(files) or 1)) as ex:
        for f, fut in [(f, ex.submit(run_one, f)) for f in files]:
            try:
                snap.update(json.loads(fut.result()))    # collectors namespace their own keys
            except Exception as e:
                snap.setdefault("_errors", []).append(f"{pathlib.Path(f).name}: {e}")
    return snap


def exit_code_for(findings) -> int:
    """Machine-consumable severity: 0 = clean, 1 = WARN only, 2 = CRIT present. Lets Task
    Scheduler / CI / scripts detect machine distress without parsing stdout."""
    levels = {f.get("level") for f in findings if isinstance(f, dict)}
    if "CRIT" in levels:
        return 2
    if "WARN" in levels:
        return 1
    return 0


def print_findings(snap):
    import rules
    findings = rules.diagnose(snap)
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
        return findings
    order = {"CRIT": 0, "WARN": 1}
    for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
        print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
              + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))
    return findings


def narrate():
    import schema, infer
    snap = snapshot()
    bundle = infer.load()                                   # loads ckpt.pt + vocab.json
    print(infer.generate_report(bundle, schema.serialize_metrics(snap)))
    print("\n--- findings (truth) ---")
    print_findings(snap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="diag", help="diag | net | report | discover")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--spawn", action="store_true", help="discover: write stub collectors")
    args = ap.parse_args()

    if args.cmd == "discover":
        import discover
        discover.main(spawn=args.spawn)
        return
    if args.cmd == "report" and not args.no_llm:
        narrate()
        return
    snap = snapshot(only="net" if args.cmd == "net" else None)
    if args.json:
        print(json.dumps(snap, indent=2))
        return 0
    import rules
    findings = rules.diagnose(snap)
    # reuse print_findings for the human output, then exit with a severity-coded status
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
    else:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
                  + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))
    return exit_code_for(findings)


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main() or 0)