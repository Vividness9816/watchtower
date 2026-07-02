# collectors/rx.py — receive-channel state. SKELETON: emits present:false until the SDR
# arrives and the FILL-ME block is completed for your hardware.
#
# The intended shape per channel — this is what rules.py will threshold on:
#   {"id": 0, "kind": "wideband"|"narrowband", "freq_hz": ..., "rate_hz": ..., "gain_db": ...,
#    "power_dbfs": ..., "noise_floor_dbfs": ..., "active": bool}
#
# "Is the channel on?" = measured channel power sits above the noise floor by a margin:
#   active = power_dbfs > noise_floor_dbfs + MARGIN_DB
# Calibrate MARGIN_DB (start ~6 dB) and the floor against YOUR antenna/environment —
# the floor is not a constant, sample it with the antenna terminated or at a quiet freq.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

MARGIN_DB = 6.0   # ponytail: fixed margin; make it per-channel if bands differ a lot

if not usb_sdrs() and not soapy_devices():
    absent("rx")
    raise SystemExit


def measure_channel(sd, ch):
    """FILL-ME: read a short burst and compute power. Reference implementation:

    import SoapySDR, numpy as np
    st = sd.setupStream(SoapySDR.SOAPY_SDR_RX, "CF32", [ch])
    sd.activateStream(st)
    buf = np.empty(8192, np.complex64)
    sr = sd.readStream(st, [buf], len(buf), timeoutUs=int(2e5))
    sd.deactivateStream(st); sd.closeStream(st)
    if sr.ret <= 0:
        return None
    power = 10 * np.log10(np.mean(np.abs(buf[:sr.ret]) ** 2) + 1e-20)
    return {
        "id": ch,
        "kind": "wideband" if sd.getSampleRate(SoapySDR.SOAPY_SDR_RX, ch) > 2e6 else "narrowband",
        "freq_hz": sd.getFrequency(SoapySDR.SOAPY_SDR_RX, ch),
        "rate_hz": sd.getSampleRate(SoapySDR.SOAPY_SDR_RX, ch),
        "gain_db": sd.getGain(SoapySDR.SOAPY_SDR_RX, ch),
        "power_dbfs": round(power, 1),
        "noise_floor_dbfs": NOISE_FLOOR,          # FILL-ME: calibrate, don't hardcode
        "active": power > NOISE_FLOOR + MARGIN_DB,
    }
    """
    return None


channels = []
# FILL-ME: open each device and measure each Rx channel:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           m = measure_channel(sd, ch)
#           if m: channels.append(m)

print(json.dumps({"rx": {"present": True, "channels": channels,
                         "note": "skeleton — fill measure_channel() for your SDR"}}))
