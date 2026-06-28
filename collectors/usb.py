# collectors/usb.py — USB device count + any device in a problem state (xHCI faults via WHEA).
import json, subprocess
ps = (r"$usb=(Get-PnpDevice -Class USB -PresentOnly -EA SilentlyContinue|Measure-Object).Count;"
      r"$bad=(Get-PnpDevice -PresentOnly -EA SilentlyContinue|"
      r"Where-Object {$_.Status -ne 'OK' -and $_.Status -ne 'Unknown'}|Measure-Object).Count;"
      r"[pscustomobject]@{devices=$usb;problems=$bad}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    print(json.dumps({"usb": json.loads(out)}))
except Exception as e:
    print(json.dumps({"usb": {"error": str(e)}}))