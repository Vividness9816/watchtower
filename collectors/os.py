# collectors/os.py — OS posture the other collectors miss: uptime, pending-reboot, CPU microcode
# (the 14900K Vmin-shift fix is 0x12B+), BIOS version, days since last update, NTP clock offset,
# host Secure Boot. All read-only; each field independently guarded so one failure can't blank
# the rest. Windows-only; a non-Windows host reports present:false.
import json, platform, subprocess

PS = r"""
$out = [ordered]@{}
try { $b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime
      $out.uptime_days = [math]::Round(((Get-Date)-$b).TotalDays,2) } catch {}
try {
  $pending = $false
  if (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') { $pending=$true }
  if (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') { $pending=$true }
  $pfro = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' -Name PendingFileRenameOperations -EA SilentlyContinue)
  if ($pfro.PendingFileRenameOperations) { $pending=$true }
  $out.pending_reboot = [bool]$pending
} catch {}
try { $r=(Get-ItemProperty 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -EA Stop)
      $mc = $r.'Update Revision'
      if ($mc -ne $null) { $out.microcode = ('0x{0:X}' -f [int64]([BitConverter]::ToUInt64(($mc+ ,0*8)[0..7],0))) } } catch {}
try { $bios=Get-CimInstance Win32_BIOS -EA Stop
      $out.bios_version = ($bios.SMBIOSBIOSVersion) } catch {}
try { $hf=Get-CimInstance Win32_QuickFixEngineering -EA Stop | Where-Object InstalledOn | Sort-Object InstalledOn | Select-Object -Last 1
      if ($hf.InstalledOn) { $out.win_update_age_days = [int]((Get-Date)-$hf.InstalledOn).TotalDays } } catch {}
try { $s=w32tm /query /status 2>$null | Select-String 'Phase Offset'
      if ($s) { $v=($s -replace '.*:\s*','' -replace 's$','').Trim()
                $out.ntp_offset_ms = [math]::Round([double]$v*1000,1) } } catch {}
# Secure Boot via the registry (no elevation, unlike Confirm-SecureBootUEFI)
try { $sb=(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State' -Name UEFISecureBootEnabled -EA Stop)
      $out.secure_boot = [bool]$sb.UEFISecureBootEnabled } catch {}
[pscustomobject]$out | ConvertTo-Json -Compress
"""


def main():
    if platform.system() != "Windows":
        print(json.dumps({"os": {"present": False, "note": "windows-only collector"}}))
        return
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        data = json.loads(out) if out else {}
        print(json.dumps({"os": data if isinstance(data, dict) else {}}))
    except Exception as e:
        print(json.dumps({"os": {"error": str(e)[:150]}}))


if __name__ == "__main__":
    main()
