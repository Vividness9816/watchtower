# collectors/services.py — Linux systemd service state (the `systemctl start xxx` units).
# Reports running-service count + any FAILED units by name. Runs natively on a Linux host
# (the Linux release) and, on a Windows host, bridges into WSL — exactly like k3s.py — so a
# Windows box can still watch the systemd services inside its WSL distro. Degrades cleanly
# when systemd is reachable nowhere.
import json, os, shutil, subprocess


def systemctl_base():
    # native Linux with systemd?
    if os.name == "posix" and shutil.which("systemctl"):
        return ["systemctl"]
    # Windows (or no native systemd): try WSL, where modern WSL2 runs systemd if enabled.
    # ADJUST like k3s.py if your distro isn't the default: prepend ["wsl","-d","Ubuntu",...]
    if shutil.which("wsl"):
        return ["wsl", "systemctl"]
    return None


def run(base, *args):
    r = subprocess.run(base + list(args) + ["--no-pager", "--no-legend"],
                       capture_output=True, text=True, timeout=20)
    return r.stdout


base = systemctl_base()
try:
    if not base:
        print(json.dumps({"services": {"present": False}}))   # no systemd anywhere reachable
        raise SystemExit
    # is systemd actually up? (WSL without systemd, or a container, answers 'offline'/errors)
    probe = subprocess.run(base + ["is-system-running"], capture_output=True, text=True, timeout=15)
    status = (probe.stdout or probe.stderr).strip()
    if probe.returncode != 0 and status in ("offline", "unknown", ""):
        print(json.dumps({"services": {"present": False, "note": f"systemd not running ({status})"}}))
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
