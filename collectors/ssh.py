# collectors/ssh.py — scrape components living on remote Linux VMs by SSHing in and running
# read-only checks (a "check" is a shell command; reading a file is just `cat`/`grep /path`).
# Shells out to the OpenSSH client (ships with Win10/11 + every Linux) exactly like k3s.py
# shells to `wsl` — no pip deps. Configure targets in ssh.config.json (see the example);
# absent config -> present:false, so this collector is a no-op until you set it up.
#
# SECURITY (this is a network + auth surface — the defaults are the safe ones):
#   * KEY-BASED AUTH ONLY. BatchMode=yes disables password prompts (no hangs, no passwords in
#     a config file). Set up an SSH key to each VM first (ssh-copy-id / authorized_keys).
#   * HOST KEYS ARE CHECKED. StrictHostKeyChecking stays on; a new VM must be in known_hosts,
#     or set "accept_new": true per target for trust-on-first-use (accept-new, never "no").
#   * Point checks at READ-ONLY commands. The collector only reads; what your commands do is
#     yours to keep read-only.
#   * One SSH session per target (all its checks run in that one session); targets run in
#     parallel with per-connect timeouts so an unreachable VM degrades instead of hanging.
import json, os, re, shlex, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.environ.get("WATCHTOWER_SSH_CONFIG", os.path.join(REPO, "ssh.config.json"))
SSH = shutil.which("ssh")
DEST_RE = re.compile(r"^[A-Za-z0-9._-]+(@[A-Za-z0-9._-]+)?$")   # user@host / host; no leading '-'


def _coerce(s):
    s = s.strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _normalize_checks(raw):
    """Each check -> {'cmd': str, 'warn'?, 'crit'?, 'unit'?}. Accepts a bare command string
    or an object with thresholds."""
    out = {}
    for name, spec in (raw or {}).items():
        if isinstance(spec, str):
            out[str(name)] = {"cmd": spec}
        elif isinstance(spec, dict) and isinstance(spec.get("cmd"), str):
            out[str(name)] = {k: spec[k] for k in ("cmd", "warn", "crit", "unit") if k in spec}
    return out


def _remote_script(checks):
    # run every check in ONE ssh session; emit "name<TAB>value" per line, each value capped
    lines = []
    for name, spec in checks.items():
        n = shlex.quote(name)
        # { cmd ; } isolates the operator's command; head -c caps output; tr flattens newlines
        lines.append(f"printf %s {n}; printf '\\t'; {{ {spec['cmd']} ; }} 2>/dev/null "
                     f"| head -c 500 | tr '\\n' ' '; printf '\\n'")
    return " ; ".join(lines)


def _scrape(target, connect_timeout):
    name = str(target.get("name") or target.get("ssh") or "?")
    dest = target.get("ssh") or target.get("host")
    checks = _normalize_checks(target.get("checks"))
    if not dest or not DEST_RE.match(str(dest)):
        return name, {"reachable": False, "error": "invalid or missing 'ssh' destination"}
    if not checks:
        return name, {"reachable": False, "error": "no checks configured"}

    strict = "accept-new" if target.get("accept_new") else "yes"
    argv = [SSH, "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no",
            "-o", f"ConnectTimeout={int(connect_timeout)}",
            "-o", f"StrictHostKeyChecking={strict}",
            "-p", str(int(target.get("port", 22)))]
    key = target.get("key")
    if key:
        argv += ["-o", "IdentitiesOnly=yes", "-i", os.path.expanduser(str(key))]
    jump = target.get("jump")                       # optional bastion/ProxyJump
    if jump and DEST_RE.match(str(jump)):
        argv += ["-J", str(jump)]
    argv += [str(dest), _remote_script(checks)]

    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=int(connect_timeout) + 12)
    except subprocess.TimeoutExpired:
        return name, {"reachable": False, "error": "timeout"}
    except Exception as e:
        return name, {"reachable": False, "error": str(e)[:150]}
    if r.returncode != 0:
        return name, {"reachable": False, "error": (r.stderr or "ssh failed").strip()[:150]}

    got = {}
    for line in r.stdout.splitlines():
        if "\t" not in line:
            continue
        cname, raw = line.split("\t", 1)
        spec = checks.get(cname, {})
        entry = {"value": _coerce(raw)}
        for k in ("warn", "crit", "unit"):
            if k in spec:
                entry[k] = spec[k]
        got[cname] = entry
    return name, {"reachable": True, "checks": got}


def main():
    if not SSH:
        print(json.dumps({"ssh": {"present": False, "note": "no ssh client on PATH"}}))
        return
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(json.dumps({"ssh": {"present": False}}))          # unconfigured = no-op
        return
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"ssh": {"error": f"ssh.config.json: {e}"}}))
        return

    targets = cfg.get("targets") if isinstance(cfg, dict) else None
    if not isinstance(targets, list) or not targets:
        print(json.dumps({"ssh": {"present": False}}))
        return
    ct = int(cfg.get("connect_timeout", 6))
    with ThreadPoolExecutor(max_workers=min(8, len(targets))) as ex:
        results = dict(ex.map(lambda t: _scrape(t, ct), targets))
    down = sum(1 for r in results.values() if not r.get("reachable"))
    print(json.dumps({"ssh": {"present": True, "down": down, "targets": results}}))


if __name__ == "__main__":
    main()
