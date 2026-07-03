# collectors/events.py — Windows event-log health signals no other collector covers:
# GPU driver resets (WDDM TDR, Event 4101 — the canonical GPU-instability signal), application
# crashes (WER 1001 / Application Error 1000), NTFS corruption (Event 55), and scheduled tasks
# whose last run failed (history.py itself runs from Task Scheduler — its silent failure is
# otherwise invisible). All time-windowed; read-only. Windows-only.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
$since = (Get-Date).AddDays(-7)
$since1 = (Get-Date).AddDays(-1)
try { $out.gpu_tdr_7d = [int]((Get-WinEvent -FilterHashtable @{LogName='System';Id=4101;StartTime=$since} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.gpu_tdr_7d = 0 }
try { $out.app_crashes_24h = [int]((Get-WinEvent -FilterHashtable @{LogName='Application';ProviderName='Application Error';Id=1000;StartTime=$since1} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.app_crashes_24h = 0 }
try { $out.ntfs_errors_24h = [int]((Get-WinEvent -FilterHashtable @{LogName='System';Id=55;StartTime=$since1} -EA SilentlyContinue | Measure-Object).Count) } catch { $out.ntfs_errors_24h = 0 }
try { $f = Get-ScheduledTask -EA Stop | Get-ScheduledTaskInfo -EA SilentlyContinue |
        Where-Object { $_.LastTaskResult -ne 0 -and $_.LastTaskResult -ne 267009 -and $_.LastRunTime -gt $since } |
        Select-Object -ExpandProperty TaskName -First 10
      $out.task_failures = @($f) } catch { $out.task_failures = @() }
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"events": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        if isinstance(data, dict):
            tf = data.get("task_failures")
            if tf is None:
                data["task_failures"] = []
            elif not isinstance(tf, list):
                data["task_failures"] = [tf]        # PS emits a bare string for a single item
        print(json.dumps({"events": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"events": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
