# collectors/me.py — Intel ME / CSME firmware version via the signed driver (no exotic access).
import json, subprocess
ps = (r"$d=Get-CimInstance Win32_PnPSignedDriver|"
      r"Where-Object {$_.DeviceName -match 'Management Engine'}|Select-Object -First 1;"
      r"if($d){[pscustomobject]@{present=$true;version=$d.DriverVersion;name=$d.DeviceName}|"
      r"ConvertTo-Json -Compress}else{'{}'}")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    print(json.dumps({"me": d or {"present": False}}))
except Exception as e:
    print(json.dumps({"me": {"error": str(e)}}))