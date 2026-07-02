# collectors/sdr.py — SDR device inventory. SKELETON: runs today (emits present:false
# with no hardware); fill the FILL-ME blocks when the SDR arrives.
# Detection is two-layer: USB VID:PID (works with zero SDR software) then SoapySDR
# enumeration (works for anything with a Soapy driver: rtl-sdr, HackRF, Lime, USRP...).
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

usb = usb_sdrs()
soapy = soapy_devices()          # None = SoapySDR not installed; [] = installed, none found

if not usb and not soapy:
    absent("sdr")
    raise SystemExit

devices = []
for kw in (soapy or []):
    dev = {"driver": kw.get("driver"), "label": kw.get("label"), "serial": kw.get("serial"),
           "rx_channels": None, "tx_channels": None}
    # FILL-ME(channel counts): opening the device is device-specific and can be slow —
    # uncomment once you know your hardware behaves:
    #   import SoapySDR
    #   sd = SoapySDR.Device(kw)
    #   dev["rx_channels"] = sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)
    #   dev["tx_channels"] = sd.getNumChannels(SoapySDR.SOAPY_SDR_TX)
    #   dev["clock_source"] = sd.getClockSource()
    devices.append(dev)

print(json.dumps({"sdr": {
    "present": True,
    "usb": usb,                          # what the bus sees, even with no drivers installed
    "soapy_installed": soapy is not None,
    "devices": devices,
}}))
