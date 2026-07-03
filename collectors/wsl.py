# collectors/wsl.py — the WSL2 utility VM this box's Docker + k3s actually run inside, which
# every other collector is blind to: vmmem working set (RAM the VM holds) and the ext4 .vhdx
# size (grows unbounded, never auto-shrinks). Read-only. Windows-only (WSL is a Windows feature).
import json, os, platform, subprocess, glob


def _vmmem_gb():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-Process 'vmmem','vmmemWSL' -EA SilentlyContinue | "
                              "Measure-Object WorkingSet64 -Sum).Sum"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return round(int(out) / 1024**3, 2) if out and out.isdigit() else None
    except Exception:
        return None


def _vhdx_gb():
    # the per-distro ext4.vhdx under %LOCALAPPDATA%\Packages\*\LocalState (Store distros) or
    # a registry BasePath; sum whatever ext4 disks exist. Best-effort, read-only.
    total = 0
    found = False
    base = os.path.expandvars(r"%LOCALAPPDATA%\Packages")
    for p in glob.glob(os.path.join(base, "*", "LocalState", "ext4.vhdx")) + \
            glob.glob(os.path.join(base, "*", "LocalState", "*.vhdx")):
        try:
            total += os.path.getsize(p)
            found = True
        except OSError:
            continue
    return round(total / 1024**3, 2) if found else None


def main():
    if platform.system() != "Windows":
        print(json.dumps({"wsl": {"present": False, "note": "windows-only collector"}}))
        return
    data = {}
    v = _vmmem_gb()
    d = _vhdx_gb()
    if v is not None:
        data["vmmem_gb"] = v
    if d is not None:
        data["vhdx_gb"] = d
    if not data:
        data = {"present": False, "note": "no running WSL VM / vhdx found"}
    print(json.dumps({"wsl": data}))


if __name__ == "__main__":
    main()
