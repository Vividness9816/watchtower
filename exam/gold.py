# gold.py — the exam's FROZEN ground truth. A self-contained copy of the original schema+rules so
# no contender (which may edit its own schema/rules) can ever influence what "correct" means.
# Snapshot generation, metric serialization, and rule-based diagnosis all live here and never change.
import random

EOS = "\x03"

# (warn, crit) thresholds — identical to original rules.THRESH; frozen.
THRESH = {
    "cpu_temp": (90, 98),
    "gpu_temp": (80, 88),
    "mem_pct":  (85, 95),
    "disk_pct": (85, 95),
}


def _g(snap, *path, default=0):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def serialize_metrics(snap: dict) -> str:
    """The exact INPUT text contenders receive for E1. Identical to original schema.serialize_metrics."""
    return "\n".join([
        f"cpu_load={int(_g(snap,'cpu','load'))} cpu_temp={int(_g(snap,'sensors','cpu_temp'))} "
        f"mem_pct={int(_g(snap,'mem','pct'))}",
        f"gpu_util={int(_g(snap,'gpu','util'))} gpu_temp={int(_g(snap,'gpu','temp'))} "
        f"gpu_power={int(_g(snap,'gpu','power'))} gpu_vram={int(_g(snap,'gpu','vram_pct'))}",
        f"disk_C={int(_g(snap,'disk','C'))} whea_errors={int(_g(snap,'whea','recent_errors'))}",
    ])


def summarize(snap: dict) -> str:
    return (f"CPU {int(_g(snap,'cpu','load'))}% / {int(_g(snap,'sensors','cpu_temp'))}C, "
            f"GPU {int(_g(snap,'gpu','util'))}% / {int(_g(snap,'gpu','temp'))}C / "
            f"{int(_g(snap,'gpu','power'))}W, RAM {int(_g(snap,'mem','pct'))}%, "
            f"disk C {int(_g(snap,'disk','C'))}%.")


def synthetic_snapshot(rng: random.Random) -> dict:
    """Identical generator to original schema.synthetic_snapshot. Held-out snapshots use seeds in a
    range disjoint from training (train builds with Random(1337)); see exam.py."""
    hot = rng.random() < 0.35
    return {
        "cpu":     {"load": rng.randint(2, 100)},
        "sensors": {"cpu_temp": rng.randint(88, 101) if hot and rng.random() < 0.5 else rng.randint(35, 80)},
        "mem":     {"pct": rng.randint(86, 99) if hot and rng.random() < 0.4 else rng.randint(10, 80)},
        "gpu":     {"util": rng.randint(0, 100),
                    "temp": rng.randint(80, 92) if hot and rng.random() < 0.5 else rng.randint(30, 78),
                    "power": rng.randint(40, 575), "vram_pct": rng.randint(3, 99)},
        "disk":    {"C": rng.randint(85, 99) if hot and rng.random() < 0.3 else rng.randint(20, 84)},
        "whea":    {"recent_errors": 0 if rng.random() < 0.85 else rng.randint(1, 5)},
    }


def diagnose(snap: dict) -> list[dict]:
    """Identical to original rules.diagnose. The DETERMINISTIC ground truth E1/E3 are scored against."""
    out = []

    def chk(value, key, label, unit="C"):
        lim = THRESH.get(key)
        if value is None or lim is None:
            return
        warn, crit = lim
        if value >= crit:
            out.append({"level": "CRIT", "what": label, "value": value, "limit": crit, "unit": unit})
        elif value >= warn:
            out.append({"level": "WARN", "what": label, "value": value, "limit": warn, "unit": unit})

    chk(_g(snap, "sensors", "cpu_temp", default=None), "cpu_temp", "CPU temp")
    chk(_g(snap, "gpu", "temp", default=None), "gpu_temp", "GPU temp")
    chk(_g(snap, "mem", "pct", default=None), "mem_pct", "RAM", "%")
    disk = snap.get("disk", {})
    if isinstance(disk, dict):
        for mount, pct in disk.items():
            chk(pct, "disk_pct", f"disk {mount}", "%")
    whea = _g(snap, "whea", "recent_errors", default=None)
    if whea:
        out.append({"level": "CRIT", "what": "WHEA hardware errors", "value": whea, "limit": "", "unit": ""})
    return out


# canonical finding "kind" each ground-truth/claim maps to — keeps the E1 checker component-agnostic
def kind_of(what: str) -> str:
    w = what.lower()
    if "cpu" in w:  return "cpu_temp"
    if "gpu" in w:  return "gpu_temp"
    if "ram" in w or "mem" in w:  return "mem"
    if "disk" in w:  return "disk"
    if "whea" in w or "hardware error" in w:  return "whea"
    return "other"


def status_of(findings: list[dict]) -> str:
    if any(f["level"] == "CRIT" for f in findings):
        return "CRITICAL"
    return "WARNING" if findings else "OK"


def demo():
    r = random.Random(0)
    hot = {"gpu": {"temp": 99}, "whea": {"recent_errors": 0}, "sensors": {"cpu_temp": 45},
           "mem": {"pct": 40}, "disk": {"C": 50}, "cpu": {"load": 10}}
    f = diagnose(hot)
    assert any(x["level"] == "CRIT" for x in f), "hot GPU must be CRIT"
    assert status_of(f) == "CRITICAL"
    assert kind_of("GPU temp") == "gpu_temp" and kind_of("disk C") == "disk"
    s = serialize_metrics(synthetic_snapshot(r))
    assert s.count("\n") == 2 and "gpu_temp=" in s
    print("gold ok")


if __name__ == "__main__":
    demo()
