# collectors/procs.py — top resource consumers, so "my machine is slow / hot / full" gets a
# named culprit. top_cpu (rough %, one 250ms sample), top_mem (working set MB), and top_gpu_vram
# (per-process VRAM via nvidia-smi — this is what names ollama.exe as the reason gpu.vram_pct is
# high, answering the chat brain's observer effect). Read-only. Windows-primary; nvidia part
# is cross-platform where nvidia-smi exists.
import json, platform, shutil, subprocess

PS = r"""
$out = [ordered]@{}
try {
  $n = [math]::Max(1,(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors)
  # two TotalProcessorTime snapshots 300ms apart -> real instantaneous CPU% per process,
  # normalized by logical-core count (Win32_PerfFormattedData_PerfProc_Process is empty on
  # some boxes; this Get-Process delta method is reliable everywhere).
  $a = @{}; Get-Process -EA SilentlyContinue | ForEach-Object { $a[$_.Id] = @($_.ProcessName, $_.TotalProcessorTime.TotalMilliseconds) }
  Start-Sleep -Milliseconds 300
  $rows = Get-Process -EA SilentlyContinue | ForEach-Object {
    if ($a.ContainsKey($_.Id)) {
      $d = $_.TotalProcessorTime.TotalMilliseconds - $a[$_.Id][1]
      [pscustomobject]@{ name=$a[$_.Id][0]; cpu_pct=[math]::Round(100*$d/300/$n,1) }
    }
  } | Where-Object { $_.name -ne 'Idle' -and $_.cpu_pct -gt 0 }
  $out.top_cpu = @($rows | Sort-Object cpu_pct -Descending | Select-Object -First 5 |
    ForEach-Object { [ordered]@{ name=$_.name; cpu_pct=$_.cpu_pct } })
} catch {}
try {
  $out.top_mem = @(Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 |
    ForEach-Object { [ordered]@{ name=$_.ProcessName; mem_mb=[int]($_.WorkingSet64/1MB) } })
} catch {}
[pscustomobject]$out | ConvertTo-Json -Depth 4 -Compress
"""


def _gpu_vram():
    smi = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
    try:
        r = subprocess.run([smi, "--query-compute-apps=process_name,used_memory",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=6)
        procs = []
        for line in r.stdout.strip().splitlines():
            if "," in line:
                name, mem = line.rsplit(",", 1)
                try:
                    procs.append({"name": name.strip(), "vram_mb": int(float(mem))})
                except ValueError:
                    continue
        return sorted(procs, key=lambda p: -p["vram_mb"])[:5]
    except Exception:
        return None


def main():
    data = {}
    if platform.system() == "Windows":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                                 capture_output=True, text=True, timeout=20).stdout.strip()
            d = json.loads(out) if out else {}
            if isinstance(d, dict):
                data.update(d)
        except Exception as e:
            data["error"] = str(e)[:150]
    tg = _gpu_vram()
    if tg is not None:
        data["top_gpu_vram"] = tg
    print(json.dumps({"procs": data}))


if __name__ == "__main__":
    main()
