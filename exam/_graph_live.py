# _graph_live.py — exam helper: prove the LIVE graph data path (sampler ring -> frame()) with
# real collector data. Fresh interpreter; ~12s runtime. Prints "graph live ok" iff frames flow.
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import live  # noqa: E402


def main():
    live.start()                      # takes one synchronous FULL snapshot immediately
    time.sleep(live.FAST_S + 7)       # let ~2 fast ticks land on top
    df = live.frame(list(live.METRICS), "5 min")
    assert list(df.columns) == ["time", "value", "series"], df.columns
    series = set(df["series"])
    # fast-tier metrics that MUST be live on this box (cpu/gpu/mem/disk are unconditional)
    for must in ["CPU temp (C)", "CPU load (%)", "GPU temp (C)", "RAM used (%)", "Disk C used (%)"]:
        assert must in series, f"missing live series: {must} (got {sorted(series)})"
    assert df["value"].notna().all(), "NaN values in live frame"
    assert len(df) >= 10, f"too few live points: {len(df)}"
    print(f"graph live ok — {len(series)} series, {len(df)} points")


if __name__ == "__main__":
    main()
