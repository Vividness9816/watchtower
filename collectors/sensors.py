# collectors/sensors.py — LibreHardwareMonitor web JSON: the WHOLE tree (every temp —
# CPU/VRM/chipset/NVMe/GPU hotspot — every fan and pump RPM), plus liquid/coolant temp.
# AIO fallback: if LHM doesn't surface a liquid temp, try liquidctl (optional dep).
# NOTE: NZXT CAM holds the Kraken's HID exclusively — liquidctl reads work when CAM is
# closed, or run LHM (it reads the Kraken too) and this collector gets it from data.json.
import json, re, os, sys, urllib.request
# our sibling usb.py/power.py would shadow pip packages (liquidctl imports pyusb as
# `usb`) — drop this script's own dir from sys.path before any third-party import
sys.path = [p for p in sys.path
            if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
LHM_URL = "http://127.0.0.1:8085/data.json"
CATEGORIES = {"Temperatures", "Fans", "Voltages", "Powers", "Clocks", "Load", "Loads",
              "Controls", "Levels", "Data", "Rates", "Throughput", "Factors", "Times"}


def walk(node, temps, fans, volts, powers, hw=""):
    name, val = node.get("Text", ""), node.get("Value", "")
    m = re.match(r"\s*(-?\d+(?:[.,]\d+)?)\s*(\S+)?", val) if val else None
    if m:
        num, unit = float(m.group(1).replace(",", ".")), (m.group(2) or "")
        key = f"{hw}: {name}" if hw else name
        if unit.endswith("C"):
            temps[key] = num
        elif unit == "RPM":
            fans[key] = int(num)
        elif unit == "V":                        # rail voltages: 12V/5V/Vcore sag = PSU warning
            volts[key] = num
        elif unit == "W":                        # CPU package / GPU board power
            powers[key] = num
    kids = node.get("Children", [])
    if kids and not m and name and name not in CATEGORIES:
        hw = name                                # nearest hardware node names the sensor
    for ch in kids:
        walk(ch, temps, fans, volts, powers, hw)


def pick(d, *words):  # first value whose key contains ALL words (case-insensitive)
    for k, v in d.items():
        if all(w in k.lower() for w in words):
            return v
    return None


def liquidctl_read():  # (liquid_temp, pump_rpm, note) — degrades to (None, None, reason)
    try:
        from liquidctl import find_liquidctl_devices
    except ImportError:
        return None, None, None
    for dev in find_liquidctl_devices():
        try:
            with dev.connect():
                st = {k.lower(): v for k, v, _ in dev.get_status()}
                liq = pick(st, "liquid") or pick(st, "coolant") or pick(st, "water")
                pump = pick(st, "pump", "speed") or pick(st, "pump", "rpm")
                return liq, pump, None
        except Exception as e:
            return None, None, (f"{dev.description}: read blocked ({type(e).__name__}) "
                                "— close NZXT CAM or run LibreHardwareMonitor")
    return None, None, None


temps, fans, volts, powers, lhm_err = {}, {}, {}, {}, None
try:
    with urllib.request.urlopen(LHM_URL, timeout=3) as r:
        walk(json.loads(r.read().decode("utf-8", "replace")), temps, fans, volts, powers)
except Exception as e:
    lhm_err = f"LHM not reachable: {e}"

cpu_matches = ([v for k, v in temps.items() if "cpu" in k.lower() and "package" in k.lower()]
               or [v for k, v in temps.items() if "cpu" in k.lower()])
liquid = pick(temps, "liquid") or pick(temps, "coolant") or pick(temps, "water")
pump = pick(fans, "pump")
if pump == 0 and liquid is None:
    pump = None      # 0-RPM 'Pump Fan' with no liquid temp = unpopulated mobo header, not the AIO
aio_note = None
if liquid is None:
    liquid, pump2, aio_note = liquidctl_read()
    pump = pump if pump is not None else pump2

out = {"cpu_temp": int(max(cpu_matches)) if cpu_matches else None,
       "fans": fans, "temps": temps, "voltages": volts, "powers": powers,
       "liquid_temp": liquid, "pump_rpm": pump}
if aio_note:
    out["aio_note"] = aio_note
if lhm_err:
    out["error"] = lhm_err                      # keeps the existing LHM-down WARN finding
print(json.dumps({"sensors": out}))
