import json, subprocess
ps = (r"$o=Get-CimInstance Win32_OperatingSystem;"
      r"$used=[math]::Round(100*($o.TotalVisibleMemorySize-$o.FreePhysicalMemory)/$o.TotalVisibleMemorySize);"
      r"$dimms=Get-CimInstance Win32_PhysicalMemory | ForEach-Object {"
      r"[pscustomobject]@{slot=$_.DeviceLocator;gb=[math]::Round($_.Capacity/1GB);"
      r"speed=$_.Speed;part=$_.PartNumber.Trim()}};"
      r"[pscustomobject]@{pct=$used;dimms=@($dimms)}|ConvertTo-Json -Compress -Depth 4")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    dimms = d["dimms"] if isinstance(d["dimms"], list) else [d["dimms"]]
    print(json.dumps({"mem": {"pct": d["pct"], "dimms": dimms}}))
except Exception as e:
    print(json.dumps({"mem": {"error": str(e)}}))