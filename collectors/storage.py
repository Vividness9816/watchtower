# collectors/storage.py — drive health + SMART depth (Get-PhysicalDisk + reliability
# counter: wear/temp/read+write error totals/power-on hours) + disk error events (24h:
# disk/stornvme/storahci — a resetting or timing-out disk logs here before SMART fails).
# Wear/temp/hours are best-effort: many consumer NVMe expose them only elevated -> null.
import json, subprocess
ps = (r"$drives=Get-PhysicalDisk | ForEach-Object {"
      r"$r=$_ | Get-StorageReliabilityCounter -EA SilentlyContinue;"
      r"[pscustomobject]@{name=$_.FriendlyName;media=$_.MediaType;"
      r"health=$_.HealthStatus.ToString();wear=$r.Wear;temp=$r.Temperature;"
      r"read_errs=$r.ReadErrorsTotal;write_errs=$r.WriteErrorsTotal;"
      r"hours=$r.PowerOnHours}};"
      r"$ev=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='disk','stornvme','storahci';Level=1,2,3;"
      r"StartTime=(Get-Date).AddDays(-1)} -EA SilentlyContinue|Measure-Object).Count;"
      r"[pscustomobject]@{drives=@($drives);events=$ev}|ConvertTo-Json -Compress -Depth 4")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=25).stdout.strip()
    d = json.loads(out)
    drives = d["drives"] if isinstance(d["drives"], list) else [d["drives"]]
    print(json.dumps({"storage": {"drives": drives, "disk_events_24h": d["events"]}}))
except Exception as e:
    print(json.dumps({"storage": {"error": str(e)}}))
