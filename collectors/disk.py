# collectors/disk.py — used% AND absolute free GB per fixed drive, pure stdlib (no PowerShell,
# no pip). free GB matters because a percentage lies across drive sizes: 95% of an 8TB drive
# (400GB free) is fine for months, 95% of a 256GB system disk (12GB free) is imminent failure —
# rules.py uses disk_free_gb to downgrade a big-drive pct-CRIT to a WARN.
import json, os, shutil, string

used, free = {}, {}
for letter in string.ascii_uppercase:
    root = f"{letter}:\\"
    if os.path.exists(root):
        try:
            u = shutil.disk_usage(root)
            used[letter] = round(100 * u.used / u.total)
            free[letter] = round(u.free / 1024**3, 1)      # GB
        except OSError:
            pass  # empty card reader / disconnected drive: skip
print(json.dumps({"disk": used, "disk_free_gb": free}))
