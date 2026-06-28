# collectors/net.py — ping 1.1.1.1 (stdlib) + link state (Get-NetAdapter).
import json, subprocess, re, platform
def ping(host="1.1.1.1"):
    n = "-n" if platform.system() == "Windows" else "-c"
    try:
        out = subprocess.run(["ping", n, "1", host], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]\s*(\d+)\s*ms", out)   # "time=12ms" / "time<1ms"
        return int(m.group(1)) if m else None
    except Exception:
        return None
def link():
    ps = (r"Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | "
          r"Select-Object -First 1 Name,LinkSpeed | ConvertTo-Json -Compress")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return json.loads(out) if out else None
    except Exception:
        return None
lk = link() or {}
print(json.dumps({"net": {"ping_ms": ping(), "target": "1.1.1.1",
                          "up": bool(lk), "name": lk.get("Name"), "speed": lk.get("LinkSpeed")}}))