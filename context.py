import json, pathlib
import rules
import rag

FACTS = pathlib.Path(__file__).parent / "system_facts.md"


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _snapshot() -> dict:
    # prefer the live sampler's cache (fresh within ~3 ticks) — a chat message then costs
    # zero collector runs; fall back to a one-shot snapshot when the sampler isn't running
    # (CLI chat.py, sysdiag report) so behavior there is unchanged
    try:
        import live
        snap, age = live.get_latest()
        if snap and age < 3 * live.FAST_S:
            return {**snap, "_snapshot_age_s": round(age, 1)}
    except Exception:
        pass
    try:
        import sysdiag
        return sysdiag.snapshot()
    except Exception as e:
        return {"_note": f"truth layer not built ({e}); showing stub.",
                "cpu": {"load": 0}, "sensors": {"cpu_temp": 0}, "mem": {"pct": 0},
                "gpu": {"util": 0, "temp": 0, "power": 0, "vram_pct": 0},
                "disk": {"C": 0}, "whea": {"recent_errors": 0}}


def snapshot_and_findings():
    snap = _snapshot()
    return snap, rules.diagnose(snap)


def build(message: str = "") -> str:
    snap, findings = snapshot_and_findings()
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        "LIVE SNAPSHOT (JSON, just collected):",
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    try:                                   # live trend digest, when the sampler is running
        import live
        trend = live.deltas()
        if trend:
            parts += ["", "RECENT TRENDS (live-sampled, last 10 min):", trend]
    except Exception:
        pass
    refs = rag.context_block(message)      # semantic retrieval replaces the keyword gate
    if refs:
        parts += ["", refs]
    return "\n".join(parts)

if __name__ == "__main__":
    out = build("how is my reverse proxy set up?")
    assert "FINDINGS" in out, "context block lost its findings"
    print(out[:800])