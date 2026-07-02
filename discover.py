# discover.py — scan the buses (USB/PCI via PnP, plus COM ports), map what's found to
# the collector that should cover it, and report coverage. `--spawn` writes a stub
# collector for any recognized device that has none (never overwrites). New stubs are
# picked up automatically by sysdiag.py's snapshot() glob — that's the whole loop:
#   plug it in -> discover sees it -> spawn stub -> fill stub -> it's in every snapshot.
import json, re, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).parent
COLLECTORS = HERE / "collectors"
sys.path.insert(0, str(COLLECTORS))
from _sdr_common import KNOWN as SDR_SIGS   # single source of truth for SDR signatures

# (VID, PID-or-None) -> (collector, label). PID None = any product from that vendor.
DEVICE_MAP = {sig: ("sdr", label) for sig, label in SDR_SIGS.items()}
DEVICE_MAP.update({
    ("1E71", None): ("sensors", "NZXT AIO (liquid temp: LHM or liquidctl)"),
    ("1B1C", None): ("lights",  "Corsair RGB (via OpenRGB SDK)"),
})

STUB = '''# collectors/{name}.py — AUTO-SPAWNED by discover.py for: {label}
# This device was seen on the bus with no collector covering it. Contract:
# print ONE json object namespaced under "{name}"; absent hardware -> {{"present": false}};
# hardware problems are values (rules.py judges them), exceptions only for real failures.
import json
print(json.dumps({{"{name}": {{"present": True, "stub": True,
                             "matched": "{label}",
                             "note": "auto-spawned stub - fill with real metrics"}}}}))
'''


def scan_pnp():
    ps = (r"Get-PnpDevice -PresentOnly -EA SilentlyContinue | "
          r"Select-Object Class,FriendlyName,InstanceId,Status | ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    devs = json.loads(out) if out else []
    return devs if isinstance(devs, list) else [devs]


def com_ports():
    ps = (r"(Get-ItemProperty 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM' -EA SilentlyContinue)."
          r"PSObject.Properties | Where-Object {$_.Name -notlike 'PS*'} | "
          r"ForEach-Object {$_.Value}")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=15).stdout
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def matches(devs):
    seen = {}
    for d in devs:
        m = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", d.get("InstanceId") or "", re.I)
        if not m:
            continue
        vid, pid = m.group(1).upper(), m.group(2).upper()
        hit = DEVICE_MAP.get((vid, pid)) or DEVICE_MAP.get((vid, None))
        if hit:
            seen.setdefault(hit, []).append(d.get("FriendlyName") or f"{vid}:{pid}")
    return seen


def main(spawn=False):
    devs = scan_pnp()
    hits = matches(devs)
    bad = [d for d in devs if (d.get("Status") or "OK") not in ("OK", "Unknown")]

    print(f"scanned {len(devs)} present PnP devices")
    for (collector, label), names in sorted(hits.items()):
        path = COLLECTORS / f"{collector}.py"
        state = "covered" if path.exists() else "NO COLLECTOR"
        print(f"  [{state:12}] {label} -> collectors/{collector}.py ({len(names)}x: {names[0]})")
        if spawn and not path.exists():
            path.write_text(STUB.format(name=collector, label=label), encoding="utf-8")
            print(f"               spawned {path.name} — fill it in, next snapshot runs it")
    for port in com_ports():
        print(f"  [candidate   ] serial port {port} — instruments here need a bespoke collector")
    for d in bad:
        print(f"  [problem     ] {d.get('FriendlyName')} status={d.get('Status')}")
    if not hits:
        print("  no mapped devices found (edit DEVICE_MAP / _sdr_common.KNOWN to teach it more)")


if __name__ == "__main__":
    main(spawn="--spawn" in sys.argv)
