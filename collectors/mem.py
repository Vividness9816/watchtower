# collectors/mem.py — physical RAM used %, per-DIMM inventory, AND commit charge % (the real
# Windows allocation-pressure metric — a box at 60% physical can still be failing allocations
# with commit exhausted) + configured DRAM speed. PartNumber is coerced through a string so a
# null (VMs / soldered RAM) doesn't drop the whole DIMM via .Trim() on $null.
import json, subprocess
ps = (r"$o=Get-CimInstance Win32_OperatingSystem;"
      r"$used=[math]::Round(100*($o.TotalVisibleMemorySize-$o.FreePhysicalMemory)/$o.TotalVisibleMemorySize);"
      # commit charge = (commit limit - free commit) / commit limit; from the OS virtual-memory
      # counters (TotalVirtualMemorySize is the commit LIMIT in KB). No perf counter needed.
      r"$commit=if($o.TotalVirtualMemorySize){[math]::Round(100*($o.TotalVirtualMemorySize-$o.FreeVirtualMemory)/$o.TotalVirtualMemorySize,1)}else{$null};"
      r"$dimms=Get-CimInstance Win32_PhysicalMemory | ForEach-Object {"
      r"[pscustomobject]@{slot=$_.DeviceLocator;gb=[math]::Round($_.Capacity/1GB);"
      r"speed=$_.Speed;configured=$_.ConfiguredClockSpeed;part=([string]$_.PartNumber).Trim()}};"
      r"$cfg=($dimms|Where-Object configured|Select-Object -First 1).configured;"
      r"[pscustomobject]@{pct=$used;commit_pct=if($commit){[math]::Round($commit,1)}else{$null};"
      r"dram_mhz=$cfg;dimms=@($dimms)}|ConvertTo-Json -Compress -Depth 4")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    dimms = d["dimms"] if isinstance(d["dimms"], list) else [d["dimms"]]
    print(json.dumps({"mem": {"pct": d["pct"], "commit_pct": d.get("commit_pct"),
                              "dram_mhz": d.get("dram_mhz"), "dimms": dimms}}))
except Exception as e:
    print(json.dumps({"mem": {"error": str(e)}}))
