# collectors/tpm.py — Get-Tpm. NOTE: full detail needs an ELEVATED shell; unelevated the
# fields come back blank -> we report an error finding. Run sysdiag elevated for TPM.
import json, subprocess
ps = (r"$t=Get-Tpm; [pscustomobject]@{present=$t.TpmPresent;ready=$t.TpmReady;"
      r"enabled=$t.TpmEnabled;owned=$t.TpmOwned}|ConvertTo-Json -Compress")
try:
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=15).stdout.strip()
    d = json.loads(out) if out else {}
    if d.get("present") is None:
        print(json.dumps({"tpm": {"error": "blank (run elevated for TPM detail)"}}))
    else:
        print(json.dumps({"tpm": d}))
except Exception as e:
    print(json.dumps({"tpm": {"error": str(e)}}))