# collectors/disk.py — used% per fixed drive, pure stdlib (no PowerShell, no pip).
import json, os, shutil, string
out = {}
for letter in string.ascii_uppercase:
    root = f"{letter}:\\"
    if os.path.exists(root):
        try:
            u = shutil.disk_usage(root)
            out[letter] = round(100 * u.used / u.total)
        except OSError:
            pass  # empty card reader / disconnected drive: skip
print(json.dumps({"disk": out}))