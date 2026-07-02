# collectors/cpu.py — core counts (CIM) + live load + REAL current clock. Win32_Processor's
# CurrentClockSpeed sticks at base clock on modern Windows, so the true clock is
# MaxClockSpeed * '% Processor Performance' (which runs >100% under turbo). Temp: sensors.py.
import json, subprocess
ps = (r"$c=Get-CimInstance Win32_Processor;"
      # modern counter first (Task Manager semantics; survives legacy-counter corruption),
      # legacy fallback, else an HONEST null — never a fabricated 0
      r"$l=(Get-Counter '\Processor Information(_Total)\% Processor Utility' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue;"
      r"if($null -eq $l){$l=(Get-Counter '\Processor(_Total)\% Processor Time' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue};"
      r"$load=if($null -ne $l){[math]::Min(100,[int]$l)}else{$null};"
      r"$perf=(Get-Counter '\Processor Information(_Total)\% Processor Performance' "
      r"-EA SilentlyContinue).CounterSamples.CookedValue;"
      r"$max=($c.MaxClockSpeed|Measure-Object -Maximum).Maximum;"
      r"$cur=if($perf){[int]($max*$perf/100)}else{$null};"
      r"[pscustomobject]@{cores=($c.NumberOfCores|Measure-Object -Sum).Sum;"
      r"logical=($c.NumberOfLogicalProcessors|Measure-Object -Sum).Sum;load=$load;"
      r"mhz=$cur;base_mhz=$max}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"cpu": {"cores": d["cores"], "logical": d["logical"], "load": d["load"],
                              "mhz": d.get("mhz"), "base_mhz": d.get("base_mhz")}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))
