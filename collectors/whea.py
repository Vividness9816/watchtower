# collectors/whea.py — Windows' own hardware-error channel (bad core/DIMM/PCIe/USB ctrl)
import json, subprocess
ps = (r"$e=Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-WHEA-Logger'} -MaxEvents 50 -ErrorAction SilentlyContinue;"
      r"$e | Select-Object TimeCreated,Id,LevelDisplayName,Message | ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    events = json.loads(out) if out else []
    if isinstance(events, dict):
        events = [events]
    errs = [e for e in events if e.get("LevelDisplayName") in ("Error", "Critical")]
    print(json.dumps({"whea": {"recent_errors": len(errs),
                               "latest": (errs[0]["Message"][:200] if errs else None)}}))
except Exception as e:
    print(json.dumps({"whea": {"error": str(e)}}))