# collectors/gpu.py — nvidia-smi (ships with the driver, zero pip). Absent GPU -> degrades.
import json, subprocess, shutil
smi = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
try:
    q = "utilization.gpu,temperature.gpu,power.draw,memory.used,memory.total"
    row = subprocess.run([smi, f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=10).stdout.strip()
    u, t, p, used, total = (x.strip() for x in row.split(","))
    print(json.dumps({"gpu": {"util": int(float(u)), "temp": int(float(t)),
                              "power": int(float(p)),
                              "vram_pct": round(100 * float(used) / float(total))}}))
except Exception as e:
    print(json.dumps({"gpu": {"error": str(e)}}))   # no NVIDIA GPU = a finding, not a crash