# collectors/gpu.py — nvidia-smi deep query (ships with the driver, zero pip):
# util/temp/power/vram (frozen keys) + fan %, P-state, SM clock vs max, power limit,
# PCIe link gen/width current-vs-max, and decoded throttle reasons. Absent GPU -> degrades.
import json, subprocess, shutil
smi = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"

THROTTLE = {0x1: "idle", 0x2: "app_clocks", 0x4: "sw_power_cap", 0x8: "hw_slowdown",
            0x10: "sync_boost", 0x20: "sw_thermal", 0x40: "hw_thermal",
            0x80: "hw_power_brake", 0x100: "display_clocks"}


def q(fields):
    # 7s x up-to-3 calls = 21s worst case, safely under sysdiag's 25s kill switch
    r = subprocess.run([smi, f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=7)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError((r.stderr or r.stdout).strip()[:200] or f"nvidia-smi rc={r.returncode}")
    return [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")]


def num(x):  # "[N/A]" / "N/A" / "" -> None
    try:
        return float(x)
    except ValueError:
        return None


def i(x):
    n = num(x)
    return None if n is None else int(n)


try:
    (u, t, p, used, total, fan, pstate, sm, smmax,
     gen, genmax, w, wmax, plim) = q(
        "utilization.gpu,temperature.gpu,power.draw,memory.used,memory.total,"
        "fan.speed,pstate,clocks.sm,clocks.max.sm,pcie.link.gen.current,pcie.link.gen.max,"
        "pcie.link.width.current,pcie.link.width.max,power.limit")
    reasons = None
    for f in ("clocks_event_reasons.active", "clocks_throttle_reasons.active"):
        try:                                       # field renamed across driver generations
            mask = int(q(f)[0], 16)
            reasons = [n for b, n in THROTTLE.items() if mask & b and n != "idle"]
            break
        except Exception:
            continue
    vram = round(100 * num(used) / num(total)) if num(used) is not None and num(total) else None
    driver = None
    try:
        driver = q("driver_version")[0] or None
    except Exception:
        pass
    print(json.dumps({"gpu": {
        "util": i(u), "temp": i(t), "power": i(p), "vram_pct": vram,
        "vram_used_mb": i(used), "vram_total_mb": i(total),
        "fan_pct": i(fan), "pstate": pstate, "sm_mhz": i(sm), "sm_max_mhz": i(smmax),
        "power_limit": i(plim), "throttle": reasons, "driver": driver,
        "pcie": {"gen": i(gen), "gen_max": i(genmax), "width": i(w), "width_max": i(wmax)},
    }}))
except FileNotFoundError:
    print(json.dumps({"gpu": {"present": False}}))  # no NVIDIA driver at all: a state, not an error
except Exception as e:
    msg = str(e)
    if "No devices were found" in msg or "couldn't communicate" in msg:
        print(json.dumps({"gpu": {"present": False}}))
    else:
        print(json.dumps({"gpu": {"error": msg}}))  # driver present but sick = a real finding
