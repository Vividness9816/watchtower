# collectors/power.py — power/boot forensics from the System event log: Kernel-Power 41
# (machine died without a clean shutdown: PSU trip, hard hang, thermal cutoff), EventLog
# 6008 (unexpected shutdown), Kernel-Processor-Power 37 (firmware throttled the CPU).
# This is the software-visible shadow of the motherboard's debug LEDs.
import json, subprocess
ps = (r"$d7=(Get-Date).AddDays(-7);$d1=(Get-Date).AddDays(-1);"
      r"$dirty=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-Kernel-Power';Id=41;StartTime=$d7}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"$unex=(Get-WinEvent -FilterHashtable @{LogName='System';Id=6008;StartTime=$d7}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"$thr=(Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-Kernel-Processor-Power';Id=37;StartTime=$d1}"
      r" -EA SilentlyContinue|Measure-Object).Count;"
      r"[pscustomobject]@{dirty=$dirty;unexpected=$unex;throttle=$thr}|ConvertTo-Json -Compress")
try:
    # internal timeout must be SHORTER than sysdiag's 25s kill so our degrade path wins the race
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"power": {"dirty_reboots_7d": d["dirty"],
                                "unexpected_shutdowns_7d": d["unexpected"],
                                "cpu_throttle_events_24h": d["throttle"]}}))
except Exception as e:
    print(json.dumps({"power": {"error": str(e)}}))
