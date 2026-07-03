# collectors/security.py — security posture: Defender real-time protection + signature age,
# firewall, BitLocker on C:, VBS/HVCI, failed-logon count (24h). Read-only; each field guarded.
# Windows-only. Some fields (BitLocker, failed logons) read fuller when elevated but degrade
# to a clean absence rather than a falsehood when they can't be read.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
try { $m=Get-MpComputerStatus -EA Stop
      $out.defender_on = [bool]$m.RealTimeProtectionEnabled
      if ($m.AntivirusSignatureLastUpdated) {
        $out.defender_sig_age_days = [int]((Get-Date)-$m.AntivirusSignatureLastUpdated).TotalDays } } catch {}
try { $fw=Get-NetFirewallProfile -EA Stop
      $out.firewall_on = [bool](($fw | Where-Object Enabled -eq $true | Measure-Object).Count -gt 0) } catch {}
try { $bl=Get-BitLockerVolume -MountPoint 'C:' -EA Stop
      $out.bitlocker_c = [string]$bl.ProtectionStatus } catch {}
try { $dg=Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard -EA Stop
      $out.vbs_on = [bool]($dg.VirtualizationBasedSecurityStatus -eq 2) } catch {}
try { $t=(Get-Date).AddDays(-1)
      $n=(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625;StartTime=$t} -EA Stop | Measure-Object).Count
      $out.failed_logons_24h = [int]$n } catch {}
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"security": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        print(json.dumps({"security": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"security": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
