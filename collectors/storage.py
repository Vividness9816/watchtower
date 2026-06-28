# collectors/storage.py — drive health + SMART (Get-PhysicalDisk + reliability counter).
# Wear/temp are best-effort: many consumer NVMe expose them only when run elevated -> null.
import json, subprocess
ps = (r"Get-PhysicalDisk | ForEach-Object {"
      r"$r=$_ | Get-StorageReliabilityCounter -EA SilentlyContinue;"
      r"[pscustomobject]@{name=$_.FriendlyName;media=$_.MediaType;"
      r"health=$_.HealthStatus.ToString();wear=$r.Wear;temp=$r.Temperature}} | ConvertTo-Json -Compress -Depth 4")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    drives = json.loads(out)
    if isinstance(drives, dict):
        drives = [drives]
    print(json.dumps({"storage": {"drives": drives}}))
except Exception as e:
    print(json.dumps({"storage": {"error": str(e)}}))