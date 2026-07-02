# collectors/antenna.py — antenna/front-end state per SDR Rx channel. SKELETON: runs today
# (emits present:false with no SDR), fill the FILL-ME block when the radio + antennas arrive.
#
# Distinct from sdr.py (device inventory) and rx.py (channel power): this reports, per
# channel, WHICH antenna port is selected, the choices available, and — where the hardware
# exposes it — received signal strength (RSSI) and standing-wave ratio (SWR).
#
# HONEST LIMIT on SWR: most receive-only SDRs (RTL-SDR, Airspy, plain HackRF Rx) have NO way
# to measure SWR — that needs a directional/return-loss bridge on a TX-capable chain (some
# USRP/Lime setups, or an external VNA/SWR meter). So swr stays null unless your hardware and
# the FILL-ME wiring actually provide it; RSSI is available on more devices via a Soapy sensor.
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)                     # only to reach _sdr_common under python -P...
from _sdr_common import usb_sdrs, soapy_devices, absent
sys.path.remove(_here)      # ...then off again, so FILL-ME imports (numpy, SoapySDR -> pyusb
#                             as `usb`) can never hit our sibling usb.py/power.py

if not usb_sdrs() and not soapy_devices():
    absent("antenna")
    raise SystemExit

antennas = []
# FILL-ME: enumerate the antenna port per Rx channel + optional RSSI/SWR sensors.
# Soapy generic version:
#   import SoapySDR
#   for kw in soapy_devices():
#       sd = SoapySDR.Device(kw)
#       for ch in range(sd.getNumChannels(SoapySDR.SOAPY_SDR_RX)):
#           sensors = sd.listSensors(SoapySDR.SOAPY_SDR_RX, ch)
#           rssi = float(sd.readSensor(SoapySDR.SOAPY_SDR_RX, ch, "RSSI")) if "RSSI" in sensors else None
#           swr = float(sd.readSensor(SoapySDR.SOAPY_SDR_RX, ch, "SWR")) if "SWR" in sensors else None
#           antennas.append({
#               "id": ch,
#               "selected": sd.getAntenna(SoapySDR.SOAPY_SDR_RX, ch),   # e.g. "RX2" / "TX/RX"
#               "options": list(sd.listAntennas(SoapySDR.SOAPY_SDR_RX, ch)),
#               "rssi_dbm": rssi,
#               "swr": swr,                 # null on receive-only radios (no return-loss bridge)
#           })

print(json.dumps({"antenna": {"present": True, "antennas": antennas,
                              "note": "skeleton — fill port/RSSI/SWR introspection for your SDR"}}))
