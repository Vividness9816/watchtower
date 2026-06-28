# collectors/cpu.py — core counts (CIM) + live load (perf counter). Temp comes from sensors.py.
import json, subprocess
ps = (r"$c=Get-CimInstance Win32_Processor;"
      r"$load=[int]((Get-Counter '\Processor(_Total)\% Processor Time' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue);"
      r"[pscustomobject]@{cores=($c.NumberOfCores|Measure-Object -Sum).Sum;"
      r"logical=($c.NumberOfLogicalProcessors|Measure-Object -Sum).Sum;load=$load}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"cpu": {"cores": d["cores"], "logical": d["logical"], "load": d["load"]}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))