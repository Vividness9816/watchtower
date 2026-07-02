# (warn, crit). THIS is your per-machine tuning knob — edit for your silicon.
THRESH = {
    "cpu_temp":    (90, 98),   # <CPU> TjMax ~100
    "gpu_temp":    (80, 88),   # <GPU> edge
    "mem_pct":     (85, 95),
    "disk_pct":    (85, 95),
    "liquid_temp": (45, 55),   # AIO coolant; >55C the loop has lost the battle
    "drive_temp":  (70, 80),   # NVMe throttle band
    "dns_ms":      (500, 2000),  # steady-state (cached) resolve; cold path is exempt
}


def _get(snap, *path):
    cur = snap
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def diagnose(snap: dict) -> list[dict]:
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

    chk(_get(snap, "sensors", "cpu_temp"), "cpu_temp", "CPU temp")
    chk(_get(snap, "gpu", "temp"), "gpu_temp", "GPU temp")
    chk(_get(snap, "mem", "pct"), "mem_pct", "RAM", "%")
    disk = snap.get("disk", {})
    if isinstance(disk, dict):
        for mount, pct in disk.items():
            chk(pct, "disk_pct", f"disk {mount}", "%")

    # WHEA / hardware errors -> straight to CRIT (no threshold; any is bad)
    whea = _get(snap, "whea", "recent_errors")
    if whea:
        out.append({"level": "CRIT", "what": "WHEA hardware errors", "value": whea, "limit": "", "unit": ""})

    # cooling rule (a rule, not a reading): hot AND a stalled fan
    cpu_temp = _get(snap, "sensors", "cpu_temp")
    fans = _get(snap, "sensors", "fans") or {}
    if cpu_temp and cpu_temp >= 90 and fans and min(fans.values()) == 0:
        out.append({"level": "CRIT", "what": "cooling (hot + stalled fan)", "value": cpu_temp, "limit": "", "unit": "C"})

    # liquid cooling: coolant temp + pump-stalled-while-warm
    liquid = _get(snap, "sensors", "liquid_temp")
    chk(liquid, "liquid_temp", "coolant temp")
    pump = _get(snap, "sensors", "pump_rpm")
    if liquid is not None and liquid >= 45 and pump == 0:
        out.append({"level": "CRIT", "what": "AIO pump (stalled while coolant warm)",
                    "value": 0, "limit": "", "unit": "RPM"})

    # GPU throttling: thermal/hardware slowdowns are findings; sw_power_cap at load is normal
    throttle = _get(snap, "gpu", "throttle") or []
    hard = [r for r in throttle if r in ("hw_thermal", "hw_slowdown", "hw_power_brake")]
    soft = [r for r in throttle if r == "sw_thermal"]
    if hard:
        out.append({"level": "CRIT", "what": "GPU hardware slowdown", "value": ",".join(hard), "limit": "", "unit": ""})
    elif soft:
        out.append({"level": "WARN", "what": "GPU thermal throttling", "value": ",".join(soft), "limit": "", "unit": ""})

    # PCIe link degraded — judged only under load (idle legitimately downshifts gen AND width)
    util = _get(snap, "gpu", "util") or 0
    pcie = _get(snap, "gpu", "pcie") or {}
    if util >= 30 and pcie.get("gen") and pcie.get("gen_max") and (
            pcie["gen"] < pcie["gen_max"] or (pcie.get("width") or 0) < (pcie.get("width_max") or 0)):
        out.append({"level": "WARN", "what": "PCIe link degraded under load",
                    "value": f"gen{pcie['gen']}x{pcie.get('width')}",
                    "limit": f"gen{pcie['gen_max']}x{pcie.get('width_max')}", "unit": ""})

    # storage depth: error totals, drive temps, disk-subsystem event noise
    for d in _get(snap, "storage", "drives") or []:
        errs = (d.get("read_errs") or 0) + (d.get("write_errs") or 0)
        if errs:
            out.append({"level": "WARN", "what": f"drive errors ({d.get('name')})",
                        "value": errs, "limit": "", "unit": ""})
        chk(d.get("temp"), "drive_temp", f"drive temp ({d.get('name')})")
    ev = _get(snap, "storage", "disk_events_24h")
    if ev:
        out.append({"level": "WARN", "what": "disk error events (24h)", "value": ev, "limit": "", "unit": ""})

    # power forensics: the machine died without a clean shutdown / firmware throttled the CPU
    dirty = max(_get(snap, "power", "dirty_reboots_7d") or 0,
                _get(snap, "power", "unexpected_shutdowns_7d") or 0)
    if dirty:
        out.append({"level": "CRIT" if dirty >= 3 else "WARN",
                    "what": "dirty shutdowns (7d)", "value": dirty, "limit": "", "unit": ""})
    thr = _get(snap, "power", "cpu_throttle_events_24h")
    if thr:
        out.append({"level": "WARN", "what": "CPU throttle events (24h)", "value": thr, "limit": "", "unit": ""})

    # NIC errors + sick resolver (cached lookups slow = resolver itself is unhealthy)
    nic_errs = (_get(snap, "net", "rx_errors") or 0) + (_get(snap, "net", "tx_errors") or 0)
    if nic_errs:
        out.append({"level": "WARN", "what": "NIC packet errors", "value": nic_errs, "limit": "", "unit": ""})
    chk(_get(snap, "net", "dns_ms"), "dns_ms", "DNS resolve", "ms")

    # internet down
    if "net" in snap and _get(snap, "net", "ping_ms") is None:
        out.append({"level": "CRIT", "what": "internet (1.1.1.1)", "value": "no reply", "limit": "", "unit": ""})

    # any collector that returned {"error": ...} is itself a (low-sev) finding
    for k, v in snap.items():
        if isinstance(v, dict) and "error" in v:
            out.append({"level": "WARN", "what": f"{k} sensor", "value": v["error"], "limit": "", "unit": ""})

    return out


def demo():  # the one runnable check: a hot GPU MUST raise CRIT
    hot = {"gpu": {"temp": 99}, "net": {"ping_ms": 12}, "whea": {"recent_errors": 0}}
    assert any(f["level"] == "CRIT" for f in diagnose(hot)), "rule engine broken"
    stalled = {"sensors": {"liquid_temp": 48, "pump_rpm": 0}}
    assert any("pump" in f["what"] for f in diagnose(stalled)), "pump rule broken"
    idle_pcie = {"gpu": {"util": 3, "pcie": {"gen": 1, "gen_max": 5, "width": 8, "width_max": 16}}}
    assert not any("PCIe" in f["what"] for f in diagnose(idle_pcie)), "idle PCIe must not flag"
    print("rules ok")


if __name__ == "__main__":
    demo()