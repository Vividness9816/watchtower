# collectors/vm.py — virtual machines and their ENCRYPTION posture. Windows/Hyper-V:
# per-VM state + whether the VM's state/migration traffic is encrypted, whether it has a
# virtual TPM, and Secure Boot (the pieces of a Hyper-V "shielded"/encrypted VM). Reports
# counts + a running-VM count for the graph. Degrades to present:false when Hyper-V is absent.
#
# NOTE: needs an ELEVATED shell for full Get-VMSecurity detail on some hosts; unelevated it
# still lists VMs and state. Linux/libvirt hosts run a different collector (see the Linux note
# in README); this is the Windows Hyper-V collector.
import json, subprocess

# Get-VM may be missing entirely (Hyper-V role not installed) -> the whole block throws and
# we degrade. Per VM we pull state + the three encryption-relevant security flags.
ps = (
    r"if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) { '[]'; exit }"
    r"$vms = Get-VM | ForEach-Object {"
    r"  $s = $null; try { $s = Get-VMSecurity -VMName $_.Name -ErrorAction SilentlyContinue } catch {}"
    r"  $fw = $null; try { $fw = Get-VMFirmware -VMName $_.Name -ErrorAction SilentlyContinue } catch {}"
    r"  [pscustomobject]@{"
    r"    name = $_.Name; state = $_.State.ToString();"
    r"    encrypted = [bool]$s.EncryptStateAndVmMigrationTraffic;"
    r"    vtpm = [bool]$s.TpmEnabled;"
    r"    shielded = [bool]$s.Shielded;"
    r"    secure_boot = ($fw.SecureBoot -eq 'On')"
    r"  }"
    r"}; @($vms) | ConvertTo-Json -Compress -Depth 4"
)
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=20).stdout.strip()
    vms = json.loads(out) if out and out != "[]" else []
    if isinstance(vms, dict):
        vms = [vms]
    if not vms:
        print(json.dumps({"vm": {"present": False}}))   # Hyper-V absent or no VMs defined
    else:
        running = sum(1 for v in vms if v.get("state") == "Running")
        encrypted = sum(1 for v in vms if v.get("encrypted"))
        print(json.dumps({"vm": {"present": True, "total": len(vms), "running": running,
                                 "encrypted": encrypted, "vms": vms}}))
except Exception as e:
    print(json.dumps({"vm": {"error": str(e)}}))
