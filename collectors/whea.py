# collectors/whea.py — Windows' own hardware-error channel (bad core/DIMM/PCIe/USB ctrl).
# recent_errors is now TIME-WINDOWED (last 7 days) so a single resolved event from years ago
# no longer produces a permanent CRIT — the reported value is CURRENT truth, not "ever, up to 50".
# corrected_7d counts Level-3 corrected machine-checks (the early-warning tier) separately.
# Severity is matched by event Level (1/2 = Critical/Error) not the localized display name, so it
# works on non-English Windows too.
import json, subprocess

# Level: 1=Critical 2=Error 3=Warning. Uncorrected hardware errors log at 1/2; corrected at 3.
# The Message field is MUI-localized text and PS 5.1 emits it in the console OEM codepage when
# redirected — force UTF-8 on both sides of the pipe or a German/Russian event byte kills the
# whole payload with a decode error exactly when WHEA events exist.
ps = (r"[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
      r"$since=(Get-Date).AddDays(-7);"
      r"$e=Get-WinEvent -FilterHashtable @{LogName='System';"
      r"ProviderName='Microsoft-Windows-WHEA-Logger';StartTime=$since} -MaxEvents 200 -ErrorAction SilentlyContinue;"
      r"$e | Select-Object TimeCreated,Id,Level,Message | ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, encoding="utf-8", errors="replace",
                         timeout=20).stdout.strip()
    events = json.loads(out) if out else []
    if isinstance(events, dict):
        events = [events]

    def _msg(e):
        m = e.get("Message")
        return m[:200] if isinstance(m, str) else None

    errs = [e for e in events if e.get("Level") in (1, 2)]
    corrected = [e for e in events if e.get("Level") == 3]
    print(json.dumps({"whea": {"recent_errors": len(errs), "corrected_7d": len(corrected),
                               "window_days": 7,
                               "latest": (_msg(errs[0]) if errs else None)}}))
except Exception as e:
    print(json.dumps({"whea": {"error": str(e)}}))
