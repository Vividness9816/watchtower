import json, glob, subprocess, sys, pathlib, argparse
HERE = pathlib.Path(__file__).parent


def snapshot(only=None) -> dict:
    snap = {}
    pattern = str(HERE / "collectors" / (f"{only}.py" if only else "*.py"))
    for f in sorted(glob.glob(pattern)):
        try:
            out = subprocess.run([sys.executable, f], capture_output=True, text=True, timeout=25).stdout
            snap.update(json.loads(out))            # collectors namespace their own keys
        except Exception as e:
            snap.setdefault("_errors", []).append(f"{pathlib.Path(f).name}: {e}")
    return snap


def print_findings(snap):
    import rules
    findings = rules.diagnose(snap)
    if not findings:
        print("OK - no findings. (collectors seen: " + ", ".join(sorted(snap)) + ")")
        return
    order = {"CRIT": 0, "WARN": 1}
    for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
        print(f"[{f['level']:4}] {f['what']}: {f['value']}{f['unit']}"
              + (f" (limit {f['limit']}{f['unit']})" if isinstance(f["limit"], (int, float)) else ""))


def narrate():
    import schema, infer
    snap = snapshot()
    bundle = infer.load()                                   # loads ckpt.pt + vocab.json
    print(infer.generate_report(bundle, schema.serialize_metrics(snap)))
    print("\n--- findings (truth) ---")
    print_findings(snap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="diag", help="diag | net | report")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    if args.cmd == "report" and not args.no_llm:
        narrate()
        return
    snap = snapshot(only="net" if args.cmd == "net" else None)
    if args.json:
        print(json.dumps(snap, indent=2))
    else:
        print_findings(snap)


if __name__ == "__main__":
    main()