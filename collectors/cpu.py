# collectors/cpu.py — core counts (CIM) + live load + REAL current clock. Win32_Processor's
# CurrentClockSpeed sticks at base clock on modern Windows, so the true clock is
# MaxClockSpeed * '% Processor Performance' (which runs >100% under turbo). Temp: sensors.py.
import json, subprocess
ps = (r"$c=Get-CimInstance Win32_Processor;"
      # ONE Get-Counter call for all three reads — each call pays a full 1s sample window, and
      # three sequential windows put this collector at ~5s, blowing the fast-tier latency
      # budget. A single call samples every path in the same window (~3s total incl. startup).
      # modern counter first (Task Manager semantics; survives legacy-counter corruption),
      # legacy fallback, else an HONEST null — never a fabricated 0
      r"$cs=(Get-Counter '\Processor Information(_Total)\% Processor Utility',"
      r"'\Processor Information(_Total)\% Processor Performance',"
      r"'\Processor Information(*)\% Processor Performance' -EA SilentlyContinue).CounterSamples;"
      r"$l=($cs|Where-Object{$_.Path -like '*% processor utility'}).CookedValue;"
      r"if($null -eq $l){$l=(Get-Counter '\Processor(_Total)\% Processor Time' -EA SilentlyContinue)."
      r"CounterSamples.CookedValue};"
      # final fallback: Win32_Processor.LoadPercentage is locale-INDEPENDENT, so `load` (which
      # feeds the frozen model input) is never null just because the perf-counter NAMES are
      # localized on a non-English Windows.
      r"if($null -eq $l){$l=(Get-CimInstance Win32_Processor -EA SilentlyContinue|"
      r"Measure-Object LoadPercentage -Average).Average};"
      r"$load=if($null -ne $l){[math]::Min(100,[int]$l)}else{$null};"
      r"$perf=($cs|Where-Object{$_.Path -like '*% processor performance' -and "
      r"$_.InstanceName -eq '_Total'}|Select-Object -First 1).CookedValue;"
      # locale-safe fallback: counter NAMES are localized on non-English Windows, but the
      # Perflib registry maps language-neutral counter INDICES (the '009' list is English on
      # EVERY locale) to the current language's names — build the localized path and retry,
      # else honest null. (Win32_PerfFormattedData_* CIM is NOT viable here: recent Win11
      # builds ship with no ADAP-populated perf classes — 'Invalid class' on this machine.)
      r"$lo=$null;$lc=$null;"
      r"if($null -eq $perf){"
      r"$e=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Perflib\009'"
      r" -EA SilentlyContinue).Counter;"
      r"$n=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Perflib\CurrentLanguage'"
      r" -EA SilentlyContinue).Counter;"
      r"$io=$null;$ic=$null;for($i=0;$i -lt $e.Count-1;$i+=2){"
      r"if($e[$i+1] -ceq 'Processor Information'){$io=$e[$i]};"
      r"if($e[$i+1] -ceq '% Processor Performance'){$ic=$e[$i]}};"
      r"if($io -and $ic){for($i=0;$i -lt $n.Count-1;$i+=2){"
      r"if($n[$i] -eq $io){$lo=$n[$i+1]};if($n[$i] -eq $ic){$lc=$n[$i+1]}}};"
      # one translated wildcard query serves BOTH the aggregate and the per-core reads (the
      # same one-sample-window economy as $cs above, so a localized box stays on budget too)
      r"if($lo -and $lc){$fs=(Get-Counter ('\'+$lo+'(*)\'+$lc)"
      r" -EA SilentlyContinue).CounterSamples;"
      r"$perf=($fs|Where-Object{$_.InstanceName -eq '_Total'}|Select-Object -First 1).CookedValue;"
      r"$fpc=$fs|Where-Object{$_.InstanceName -notmatch '_Total'}}};"
      r"$max=($c.MaxClockSpeed|Measure-Object -Maximum).Maximum;"
      r"$cur=if($perf){[int]($max*$perf/100)}else{$null};"
      # per-core % Processor Performance -> the fastest single core right now (hybrid P-cores
      # boost well past the fleet average, which sits below base under mixed load); sampled in
      # the same $cs window above — or from the translated fallback window on a localized box
      r"$pc=$cs|Where-Object{$_.Path -like '*% processor performance' -and "
      r"$_.InstanceName -notmatch '_Total'};"
      r"if($null -eq $pc){$pc=$fpc};"
      r"$pk=if($pc){($pc.CookedValue|Measure-Object -Maximum).Maximum}else{$null};"
      r"$maxcore=if($pk){[int]($max*$pk/100)}else{$null};"
      r"[pscustomobject]@{cores=($c.NumberOfCores|Measure-Object -Sum).Sum;"
      r"logical=($c.NumberOfLogicalProcessors|Measure-Object -Sum).Sum;load=$load;"
      r"mhz=$cur;max_core_mhz=$maxcore;base_mhz=$max}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out)
    print(json.dumps({"cpu": {"cores": d["cores"], "logical": d["logical"], "load": d["load"],
                              "mhz": d.get("mhz"), "max_core_mhz": d.get("max_core_mhz"),
                              "base_mhz": d.get("base_mhz")}}))
except Exception as e:
    print(json.dumps({"cpu": {"error": str(e)}}))
