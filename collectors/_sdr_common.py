# collectors/_sdr_common.py — shared SDR probe. Underscore prefix = snapshot() skips it
# (it's a library, not a collector). Used by sdr.py / rx.py / tx.py / tuner.py.
import json, re, subprocess

# USB signatures of common SDRs; PID None = any product from that vendor.
KNOWN = {
    ("0BDA", "2832"): "RTL-SDR (RTL2832U)",
    ("0BDA", "2838"): "RTL-SDR (RTL2832U)",
    ("1D50", "6089"): "HackRF One",
    ("1D50", "60A1"): "Airspy",
    ("1D50", "6108"): "LimeSDR",
    ("0456", "B673"): "ADALM-Pluto",
    ("2500", None):   "Ettus USRP",
    ("1DF7", None):   "SDRplay RSP",
}


def usb_sdrs():
    """SDRs visible on USB right now (no SDR libraries needed) -> [labels]."""
    ps = r"Get-PnpDevice -PresentOnly -EA SilentlyContinue | Select-Object -ExpandProperty InstanceId"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    found = []
    for vid, pid in set(re.findall(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", out, re.I)):
        label = KNOWN.get((vid.upper(), pid.upper())) or KNOWN.get((vid.upper(), None))
        if label and label not in found:
            found.append(label)
    return found


def soapy_devices():
    """Enumerate via SoapySDR if installed -> [ {driver, label, serial, ...} ] or None."""
    try:
        import SoapySDR
    except ImportError:
        return None
    return [dict(kw) for kw in SoapySDR.Device.enumerate()]


def absent(namespace):
    """The degrade contract: hardware not present is a STATE, not an error finding."""
    print(json.dumps({namespace: {"present": False}}))
