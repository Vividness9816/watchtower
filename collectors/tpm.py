# collectors/tpm.py — TPM presence/version via `tpmtool getdeviceinformation`, which returns the
# full truth WITHOUT an elevated shell (unlike Get-Tpm, whose fields come back blank unelevated).
# Falls back to Get-Tpm if tpmtool is unavailable (older Windows). Read-only.
import json, re, subprocess


def _from_tpmtool():
    out = subprocess.run(["tpmtool", "getdeviceinformation"],
                         capture_output=True, text=True, timeout=15).stdout
    if not out.strip():
        return None
    def grab(label):
        m = re.search(rf"{re.escape(label)}\s*:?\s*(.+)", out, re.I)
        return m.group(1).strip() if m else None
    present = grab("TPM Present")
    if present is None:
        return None
    tob = lambda s: None if s is None else s.strip().lower() in ("true", "yes", "1")
    return {"present": tob(present), "version": grab("TPM Version"),
            "manufacturer": grab("TPM Manufacturer ID") or grab("Manufacturer"),
            "ready": tob(grab("Ready For Storage")) if grab("Ready For Storage") else tob(grab("Is Initialized"))}


def _from_gettpm():
    ps = (r"$t=Get-Tpm; [pscustomobject]@{present=$t.TpmPresent;ready=$t.TpmReady;"
          r"enabled=$t.TpmEnabled;owned=$t.TpmOwned}|ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    return d if d.get("present") is not None else None


def _from_pnp():
    # last-resort, locale-safe AND unelevated: tpmtool's console labels are MUI-localized (its
    # English-label regexes above match nothing on a German/Japanese box) and Get-Tpm is blank
    # unelevated — but device instance IDs are never localized, and every TPM 2.0 enumerates
    # as ACPI device MSFT0101. TPM 1.2 (PNP0C31) stays None -> the honest error, not a false no.
    ps = ("$p=@(Get-CimInstance Win32_PnPEntity -Filter \"PNPDeviceID LIKE '%MSFT0101%'\").Count -gt 0;"
          "[pscustomobject]@{present=$p;version=$(if($p){'2.0'}else{$null});manufacturer=$null;ready=$null}"
          "|ConvertTo-Json -Compress")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    return d if d.get("present") else None


def main():
    try:
        d = _from_tpmtool()
    except Exception:
        d = None
    if d is None:
        try:
            d = _from_gettpm()
        except Exception:
            d = None
    if d is None:
        try:
            d = _from_pnp()
        except Exception:
            d = None
    if d is None:
        print(json.dumps({"tpm": {"error": "TPM detail unavailable (tpmtool + Get-Tpm both blank)"}}))
    else:
        print(json.dumps({"tpm": d}))


if __name__ == "__main__":
    main()
