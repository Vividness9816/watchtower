# (warn, crit). THIS is your per-machine tuning knob — edit for your silicon.
THRESH = {
    "cpu_temp":    (90, 98),   # <CPU> TjMax ~100
    "gpu_temp":    (80, 88),   # <GPU> edge
    "mem_pct":     (85, 95),
    "disk_pct":    (85, 95),
    "liquid_temp": (45, 55),   # AIO coolant; >55C the loop has lost the battle
    "drive_temp":  (70, 80),   # NVMe throttle band
    "dns_ms":      (500, 2000),  # steady-state (cached) resolve
    "dns_cold_ms": (5000, 15000),  # resolver->upstream path; this LAN has shown 11s legit-slow
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

    # cooling rule (a rule, not a reading): hot AND the fan that matters is stalled.
    # Unpopulated headers legitimately read 0 RPM forever, so judge only the CPU fan(s) —
    # or a total stall (every reported fan at 0).
    cpu_temp = _get(snap, "sensors", "cpu_temp")
    fans = _get(snap, "sensors", "fans")
    fans = fans if isinstance(fans, dict) else {}   # remote JSON may send a non-dict; don't crash
    cpu_fans = {k: v for k, v in fans.items()
                if "cpu" in str(k).lower() and isinstance(v, (int, float))}
    numeric = [v for v in fans.values() if isinstance(v, (int, float))]
    if cpu_temp and cpu_temp >= 90 and numeric and (
            (cpu_fans and min(cpu_fans.values()) == 0) or max(numeric) == 0):
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
        if not isinstance(d, dict):     # PS 5.1 wraps an empty pipeline as [null]
            continue
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

    # systemd: a failed unit is a clear signal; name the units so the fix is obvious
    failed = _get(snap, "services", "failed")
    if failed:
        units = _get(snap, "services", "failed_units") or []
        names = ", ".join(str(u) for u in units[:5]) if isinstance(units, list) else ""
        out.append({"level": "CRIT" if failed >= 3 else "WARN", "what": "failed services",
                    "value": names or failed, "limit": "", "unit": ""})

    # remote SSH-scraped VMs: unreachable target -> WARN; each check carries its own thresholds.
    # Fully type-guarded: this block sees semi-trusted JSON from a monitored box over the remote
    # ingest path, so a malformed checks/warn/crit must not crash diagnose().
    ssh_targets = _get(snap, "ssh", "targets")
    if isinstance(ssh_targets, dict):
        for tname, t in ssh_targets.items():
            if not isinstance(t, dict):
                continue
            if t.get("reachable") is False:
                out.append({"level": "WARN", "what": f"SSH target unreachable ({tname})",
                            "value": t.get("error", "no reply"), "limit": "", "unit": ""})
                continue
            checks = t.get("checks")
            if not isinstance(checks, dict):
                continue
            for cname, c in checks.items():
                if not isinstance(c, dict) or not isinstance(c.get("value"), (int, float)):
                    continue
                v = c["value"]
                warn = c["warn"] if isinstance(c.get("warn"), (int, float)) else None
                crit = c["crit"] if isinstance(c.get("crit"), (int, float)) else None
                unit = c.get("unit", "")
                # direction inferred from the thresholds: crit < warn means lower-is-worse
                # (cert days left, free GB) -> fire when value drops BELOW; else higher-is-worse.
                low = warn is not None and crit is not None and crit < warn
                hit = (lambda th: v <= th) if low else (lambda th: v >= th)
                if crit is not None and hit(crit):
                    out.append({"level": "CRIT", "what": f"{tname}:{cname}", "value": v, "limit": crit, "unit": unit})
                elif warn is not None and hit(warn):
                    out.append({"level": "WARN", "what": f"{tname}:{cname}", "value": v, "limit": warn, "unit": unit})

    # NIC errors + sick resolver (cached lookups slow = resolver itself is unhealthy)
    nic_errs = (_get(snap, "net", "rx_errors") or 0) + (_get(snap, "net", "tx_errors") or 0)
    if nic_errs:
        out.append({"level": "WARN", "what": "NIC packet errors", "value": nic_errs, "limit": "", "unit": ""})
    chk(_get(snap, "net", "dns_ms"), "dns_ms", "DNS resolve", "ms")
    chk(_get(snap, "net", "dns_cold_ms"), "dns_cold_ms", "DNS cold resolve", "ms")
    # resolver DEAD (dns_ms None while raw-IP ping works) = "internet up but nothing loads"
    if "net" in snap and _get(snap, "net", "dns_ms") is None and _get(snap, "net", "ping_ms") is not None:
        out.append({"level": "CRIT", "what": "DNS resolution (ping OK, resolve fails)",
                    "value": "no answer", "limit": "", "unit": ""})

    # internet down
    if "net" in snap and _get(snap, "net", "ping_ms") is None:
        out.append({"level": "CRIT", "what": "internet (1.1.1.1)", "value": "no reply", "limit": "", "unit": ""})

    # any collector that returned {"error": ...} is itself a (low-sev) finding
    for k, v in snap.items():
        if isinstance(v, dict) and "error" in v:
            out.append({"level": "WARN", "what": f"{k} sensor", "value": v["error"], "limit": "", "unit": ""})

    # a collector that died outright (timeout/bad JSON) must surface too, not vanish
    for msg in snap.get("_errors") or []:
        out.append({"level": "WARN", "what": "collector failed", "value": msg, "limit": "", "unit": ""})

    return out


def demo():  # the one runnable check: a hot GPU MUST raise CRIT
    hot = {"gpu": {"temp": 99}, "net": {"ping_ms": 12}, "whea": {"recent_errors": 0}}
    assert any(f["level"] == "CRIT" for f in diagnose(hot)), "rule engine broken"
    stalled = {"sensors": {"liquid_temp": 48, "pump_rpm": 0}}
    assert any("pump" in f["what"] for f in diagnose(stalled)), "pump rule broken"
    idle_pcie = {"gpu": {"util": 3, "pcie": {"gen": 1, "gen_max": 5, "width": 8, "width_max": 16}}}
    assert not any("PCIe" in f["what"] for f in diagnose(idle_pcie)), "idle PCIe must not flag"
    loaded_pcie = {"gpu": {"util": 95, "pcie": {"gen": 1, "gen_max": 5, "width": 8, "width_max": 16}}}
    assert any("PCIe" in f["what"] for f in diagnose(loaded_pcie)), "loaded PCIe must flag"
    throttling = {"gpu": {"throttle": ["hw_thermal"]}}
    assert any(f["level"] == "CRIT" and "slowdown" in f["what"] for f in diagnose(throttling)), "throttle rule broken"
    bad_drive = {"storage": {"drives": [None, {"name": "X", "read_errs": 3, "write_errs": 0}]}}
    assert any("drive errors" in f["what"] for f in diagnose(bad_drive)), "drive-error rule broken (or [null] crash)"
    dead_dns = {"net": {"ping_ms": 12, "dns_ms": None}}
    assert any("DNS resolution" in f["what"] for f in diagnose(dead_dns)), "dead-resolver rule broken"
    unpopulated = {"sensors": {"cpu_temp": 95, "fans": {"CPU Fan": 1500, "System Fan #5": 0}}}
    assert not any("cooling" in f["what"] for f in diagnose(unpopulated)), "empty header must not CRIT"
    died = {"_errors": ["net.py: timeout"]}
    assert any("collector failed" in f["what"] for f in diagnose(died)), "_errors must surface"
    svc = {"services": {"failed": 2, "failed_units": ["nginx.service", "sshd.service"]}}
    assert any("failed services" in f["what"] and "nginx" in str(f["value"]) for f in diagnose(svc)), "service rule broken"
    ssh_snap = {"ssh": {"targets": {
        "db-vm": {"reachable": True, "checks": {
            "disk_root_pct": {"value": 96, "warn": 85, "crit": 95, "unit": "%"},   # high-is-worse
            "cert_days_left": {"value": 3, "warn": 30, "crit": 7, "unit": "d"}}},   # low-is-worse
        "web-vm": {"reachable": False, "error": "timeout"}}}}
    sf = diagnose(ssh_snap)
    assert any(f["level"] == "CRIT" and "db-vm:disk_root_pct" in f["what"] for f in sf), "ssh high threshold broken"
    assert any(f["level"] == "CRIT" and "db-vm:cert_days_left" in f["what"] for f in sf), "ssh low-is-worse broken"
    assert any("unreachable (web-vm)" in f["what"] for f in sf), "ssh unreachable rule broken"
    # a healthy cert (many days left) must NOT fire, and malformed remote input must not crash
    assert not any("cert" in f["what"] for f in diagnose({"ssh": {"targets": {"x": {"reachable": True,
        "checks": {"cert_days_left": {"value": 90, "warn": 30, "crit": 7}}}}}})), "healthy cert false-fired"
    for bad in ([1, 2, 3], "pwn", 5):
        diagnose({"ssh": {"targets": {"x": {"reachable": True, "checks": bad}}}})       # no crash
    diagnose({"ssh": {"targets": {"x": {"reachable": True, "checks": {"c": {"value": 9, "crit": "x"}}}}}})
    print("rules ok")


if __name__ == "__main__":
    demo()