# tests/run_all.py — the single test entrypoint (local + CI): every module self-test, the
# security regression suite, and the tests/ fixtures + stress. Exits nonzero on any failure.
# Needs only gradio + pandas + sqlite-vec (no torch); tests/torch_smoke.py covers the GPT stack.
import pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUITE = [
    ["schema.py"],
    ["rules.py"],
    ["notes.py"],
    ["search.py"],
    ["collectors/docker.py", "--test"],
    ["tests/test_linux_parsers.py"],
    ["tests/test_concurrency.py"],
    ["test_security.py"],           # imports app -> starts the live sampler (slowest, so last-ish)
    ["live.py"],                    # runs the real local sampler end to end
]


def main():
    failed = []
    for args in SUITE:
        name = " ".join(args)
        t0 = time.time()
        r = subprocess.run([sys.executable, *args], cwd=ROOT)
        verdict = "ok" if r.returncode == 0 else f"FAIL (exit {r.returncode})"
        print(f"[run_all] {name}: {verdict} ({time.time() - t0:.1f}s)", flush=True)
        if r.returncode:
            failed.append(name)
    if failed:
        print(f"[run_all] {len(failed)}/{len(SUITE)} suites FAILED: {', '.join(failed)}")
        return 1
    print(f"[run_all] all {len(SUITE)} suites ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
