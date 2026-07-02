import json, pathlib
import rules
import rag

FACTS = pathlib.Path(__file__).parent / "system_facts.md"


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _snapshot(host=None) -> dict:
    # prefer the live sampler's cache (fresh within ~3 ticks) — a chat message then costs
    # zero collector runs; fall back to a one-shot snapshot when the sampler isn't running
    # (CLI chat.py, sysdiag report) so behavior there is unchanged. `host` selects which
    # machine's cache to read (the GUI passes the selected host explicitly, so concurrent
    # tabs viewing different hosts never clobber each other via a shared global).
    try:
        import live
        snap, age, full_age = live.get_latest(host)
        # REMOTE mode: the cache is the ONLY truth — falling back to local collectors
        # would silently describe the monitoring computer instead of the monitored one.
        if live.REMOTE:
            if not snap:
                return {"_note": "remote mode: no snapshots received from the agent yet"}
            out = {**snap, "_snapshot_age_s": round(min(age, 9999), 1),
                   "_full_fleet_age_s": round(min(full_age, 9999), 1)}
            if age > 3 * live.FAST_S:
                out["_note"] = f"agent stopped shipping {round(age)}s ago — data is STALE"
            return out
        if snap and age < 3 * live.FAST_S:
            return {**snap, "_snapshot_age_s": round(age, 1),
                    "_full_fleet_age_s": round(min(full_age, 9999), 1)}
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


def snapshot_and_findings(host=None):
    snap = _snapshot(host)
    try:
        return snap, rules.diagnose(snap)
    except Exception as e:
        # REMOTE snapshots are semi-trusted JSON from another machine; a malformed field
        # must not crash the 5s GUI panel / chat. Degrade to a single visible finding.
        return snap, [{"level": "WARN", "what": "rules engine",
                       "value": f"could not evaluate snapshot: {e}", "limit": "", "unit": ""}]


def build(message: str = "", host=None) -> str:
    snap, findings = snapshot_and_findings(host)
    age, full_age = snap.get("_snapshot_age_s"), snap.get("_full_fleet_age_s")
    label = ("LIVE SNAPSHOT (JSON, just collected):" if age is None else
             f"LIVE SNAPSHOT (JSON; fast metrics ~{age}s old, "
             f"full fleet — net/docker/whea/power/storage — ~{full_age}s old):")
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        label,
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    try:                                   # live trend digest, when the sampler is running
        import live
        trend = live.deltas(host=host)
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