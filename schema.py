import random

EOS = "\x03"  # end-of-document marker; one reserved control char


def _g(snap, *path, default=0):
    """Dig snap['a']['b']... returning default (0) for any missing/None step."""
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _i(snap, *path):
    """int() of a dug metric, but SAFE: a hostile non-numeric leaf (list/dict/str from a sick or
    spoofed remote collector) coerces to 0 instead of raising — summarize()/serialize feed the UI
    panel and the model, and must never crash on a malformed snapshot. Identical to int(_g(...))
    for the normal numeric case, so the training corpus is unchanged."""
    import math
    v = _g(snap, *path)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0
    if isinstance(v, float) and not math.isfinite(v):     # NaN/inf from a sick collector -> 0
        return 0
    return int(v)


def serialize_metrics(snap: dict) -> str:
    """The exact INPUT text the model trains and runs on. Keep it stable forever."""
    return "\n".join([
        f"cpu_load={_i(snap,'cpu','load')} cpu_temp={_i(snap,'sensors','cpu_temp')} "
        f"mem_pct={_i(snap,'mem','pct')}",
        f"gpu_util={_i(snap,'gpu','util')} gpu_temp={_i(snap,'gpu','temp')} "
        f"gpu_power={_i(snap,'gpu','power')} gpu_vram={_i(snap,'gpu','vram_pct')}",
        f"disk_C={_i(snap,'disk','C')} whea_errors={_i(snap,'whea','recent_errors')}",
    ])


def summarize(snap: dict) -> str:
    """One-line human summary embedded in every report (training label + runtime)."""
    return (f"CPU {_i(snap,'cpu','load')}% / {_i(snap,'sensors','cpu_temp')}C, "
            f"GPU {_i(snap,'gpu','util')}% / {_i(snap,'gpu','temp')}C / "
            f"{_i(snap,'gpu','power')}W, RAM {_i(snap,'mem','pct')}%, "
            f"disk C {_i(snap,'disk','C')}%.")


def synthetic_snapshot(rng: random.Random) -> dict:
    """A plausible random machine state in the SAME nested shape the real collectors emit.
    ~35% are nudged hot so the corpus contains WARNING/CRITICAL examples to learn from."""
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


def demo():  # train/serve symmetry check: real-shaped and synthetic-shaped serialize the same way
    rng = random.Random(0)
    real = {"cpu": {"load": 5}, "sensors": {"cpu_temp": 45}, "mem": {"pct": 43},
            "gpu": {"util": 3, "temp": 39, "power": 64, "vram_pct": 12},
            "disk": {"C": 95}, "whea": {"recent_errors": 0}}
    for snap in (synthetic_snapshot(rng), real):
        s = serialize_metrics(snap)
        assert s.count("\n") == 2 and "cpu_load=" in s, "serialization shape drifted"
    print("schema ok")


if __name__ == "__main__":
    demo()