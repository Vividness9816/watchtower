# collectors/lights.py — board/RGB light state via the OpenRGB SDK server (127.0.0.1:6742).
# Reads every registered RGB device (motherboard, GPU, DRAM, strips) and how many LEDs are
# actually lit. HONEST LIMIT: POST/EZ-Debug LEDs (CPU/DRAM/VGA/BOOT) are hardware-driven
# during boot and NOT software-readable — for that failure class see power.py (dirty
# reboots) and whea.py. RGB state IS still diagnostic: a dead zone = dead header/device.
# Degrades to a note (not an error) — dark RGB is not a health warning.
import json
try:
    from openrgb import OpenRGBClient
    c = OpenRGBClient(address="127.0.0.1", port=6742, name="sysdiag")
    devs = []
    for d in c.devices:
        lit = sum(1 for led in d.colors if led.red or led.green or led.blue)
        devs.append({"name": d.name, "type": d.type.name, "leds": len(d.colors), "lit": lit})
    c.disconnect()
    print(json.dumps({"lights": {"devices": devs}}))
except ImportError:
    print(json.dumps({"lights": {"note": "openrgb-python not installed (optional)"}}))
except Exception as e:
    print(json.dumps({"lights": {"note": f"OpenRGB SDK not reachable: {e}"}}))
