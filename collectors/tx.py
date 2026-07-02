# collectors/tx.py — transmit-chain state. SKELETON: emits present:false until filled.
#
# Target shape per channel:
#   {"id": 0, "enabled": bool, "freq_hz": ..., "rate_hz": ..., "gain_db": ...}
#
# HONEST LIMIT: most SDRs cannot self-report actual RF power leaving the antenna port —
# "enabled + configured" is what the API gives you. If you need proof of emission, the
# two real options are (a) a directional coupler feeding one of your OWN Rx channels
# (then rx.py's power-above-floor check IS your Tx confirmation), or (b) a hardware
# power meter. Wire whichever you pick into verify_emission() below.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

if not usb_sdrs() and not soapy_devices():
    absent("tx")
    raise SystemExit


def verify_emission(ch):
    """FILL-ME (optional): loopback/coupler check that Tx RF is actually present."""
    return None


channels = []
# FILL-ME: enumerate Tx channels and their configured state:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_TX)):
#           channels.append({
#               "id": ch,
#               "freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_TX, ch),
#               "rate_hz": sd.getSampleRate(SoapySDR.SOAPY_SDR_TX, ch),
#               "gain_db": sd.getGain(SoapySDR.SOAPY_SDR_TX, ch),
#               "enabled": None,        # device-specific: stream active / PA enabled
#               "emission_verified": verify_emission(ch),
#           })

print(json.dumps({"tx": {"present": True, "channels": channels,
                         "note": "skeleton — fill Tx enumeration for your SDR"}}))
