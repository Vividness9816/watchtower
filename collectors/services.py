# collectors/services.py — Linux systemd service state (the `systemctl start xxx` units).
# Reports running-service count + any FAILED units by name. Runs natively on a Linux host
# (the Linux release) and, on a Windows host, bridges into WSL — exactly like k3s.py — so a
# Windows box can still watch the systemd services inside its WSL distro. Degrades cleanly
# when systemd is reachable nowhere (WSL1, no distro, systemd disabled).
#
# Two Windows gotchas this handles: (1) systemctl output is UTF-8 (the '●' status glyph is
# 0xE2 0x97 0x8F) — we decode utf-8/replace, not the cp1252 locale codec, or a failed unit's
# bullet crashes the decode. (2) `systemctl list-units` prints a leading '●' column for
# troubled units — `--plain` drops it so we parse the real unit name.
import json, os, shutil, subprocess

# a real systemd `is-system-running` answer is one of these; anything else (command-not-found,
# wsl's UTF-16 "no distribution" banner, empty) means systemd isn't actually reachable here
VALID = {"running", "degraded", "maintenance", "starting", "stopping", "initializing"}


def systemctl_base():
    if os.name == "posix" and shutil.which("systemctl"):
        return ["systemctl"]                        # native Linux with systemd
    # Windows (or no native systemd): try WSL, where modern WSL2 runs systemd if enabled.
    # ADJUST like k3s.py if your distro isn't the default: prepend ["wsl","-d","Ubuntu",...]
    if shutil.which("wsl"):
        return ["wsl", "systemctl"]
    return None


def run(base, *args):
    r = subprocess.run(base + list(args) + ["--plain", "--no-pager", "--no-legend"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=20)
    return r.stdout or ""


base = systemctl_base()
try:
    if not base:
        print(json.dumps({"services": {"present": False}}))   # no systemd anywhere reachable
        raise SystemExit
    probe = subprocess.run(base + ["is-system-running"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
    status = (probe.stdout or "").strip()
    if status not in VALID:            # command-not-found / no-distro / WSL1 / systemd disabled
        print(json.dumps({"services": {"present": False, "note": f"systemd not reachable ({status or 'no answer'})"}}))
        raise SystemExit
    running = [ln.split()[0] for ln in run(base, "list-units", "--type=service",
                                           "--state=running").splitlines() if ln.strip()]
    failed = [ln.split()[0] for ln in run(base, "list-units", "--type=service",
                                          "--state=failed").splitlines() if ln.strip()]
    print(json.dumps({"services": {"present": True, "running": len(running),
                                   "failed": len(failed), "failed_units": failed,
                                   "state": status}}))
except SystemExit:
    raise
except Exception as e:
    print(json.dumps({"services": {"error": str(e)}}))
