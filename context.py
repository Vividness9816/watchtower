import json, pathlib
import rules

FACTS = pathlib.Path(__file__).parent / "system_facts.md"
HOMELAB = pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md"  # optional; missing = skipped

# Only inject the ~9k-token homelab doc when the question is actually about it,
# instead of paying that on every hardware question (it overflowed num_ctx before).
# Generic infra terms; add your own service names locally if you want the gate to fire on them.
HOMELAB_TRIGGERS = ("docker", "container", "homelab", "compose", "k3s", "kubernetes",
                    "traefik", "grafana", "nginx", "vpn", "reverse proxy", "proxy")


def _wants_homelab(message: str) -> bool:
    return any(t in message.lower() for t in HOMELAB_TRIGGERS)


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _snapshot() -> dict:
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
    if _wants_homelab(message):  # gate: ~9k tokens, only when the question is homelab-related
        homelab = _read(HOMELAB)
        if homelab:
            parts += ["", "HOMELAB REFERENCE (HOMELAB-COMPLETE-SETUP.md):", homelab]
    return "\n".join(parts)


if __name__ == "__main__":
    assert _wants_homelab("how's my docker stack?") and not _wants_homelab("is my GPU hot?")
    print(build())