# collectors/tuner.py — tuner/frontend state. SKELETON: emits present:false until filled.
#
# Target shape per tuner:
#   {"id": 0, "type": "R820T2"|..., "locked": bool, "ppm": ..., "agc": bool,
#    "lo_freq_hz": ..., "bandwidth_hz": ...}
#
# "locked" = the PLL achieved lock at the requested LO frequency — the tuner-level
# equivalent of "is this input on". Most drivers surface it as a failed setFrequency /
# a status flag; rtl-sdr exposes tuner type + PPM directly (librtlsdr get_tuner_type).
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sdr_common import usb_sdrs, soapy_devices, absent

if not usb_sdrs() and not soapy_devices():
    absent("tuner")
    raise SystemExit

tuners = []
# FILL-ME: per-driver frontend introspection. Soapy generic version:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           tuners.append({
#               "id": ch,
#               "type": kw.get("tuner") or kw.get("driver"),
#               "lo_freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_RX, ch, "RF"),
#               "bandwidth_hz": sd.getBandwidth(SoapySDR.SOAPY_SDR_RX, ch),
#               "agc": bool(sd.getGainMode(SoapySDR.SOAPY_SDR_RX, ch)),
#               "ppm": sd.getFrequencyCorrection(SoapySDR.SOAPY_SDR_RX, ch),
#               "locked": None,   # FILL-ME: driver-specific lock/status sensor, e.g.
#                                 # "lo_locked" in sd.listSensors(SOAPY_SDR_RX, ch)
#           })

print(json.dumps({"tuner": {"present": True, "tuners": tuners,
                            "note": "skeleton — fill frontend introspection for your SDR"}}))
