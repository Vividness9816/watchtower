# collectors/docker.py — Docker container state + live resource usage, PARSED to numbers.
# Merges `docker ps` (name/image/status/ports) with `docker stats` (cpu/mem/net/block I/O/pids).
import json, re, subprocess, shutil, os, sys

_DEFAULT = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
DOCKER = shutil.which("docker.exe") or (_DEFAULT if os.path.exists(_DEFAULT) else None)

# go-units: memory uses binary (KiB/MiB/GiB); net & block I/O use decimal (kB/MB/GB).
_UNITS = {"b": 1, "kb": 1000, "mb": 1000**2, "gb": 1000**3, "tb": 1000**4,
          "kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4}


def _bytes(s):
    if not s:
        return None
    m = re.match(r"\s*([\d.]+)\s*([a-zA-Z]*)", s.strip())
    if not m or not m.group(1):
        return None
    return int(float(m.group(1)) * _UNITS.get(m.group(2).lower() or "b", 1))


def _pct(s):
    if not s:
        return None
    try:
        return float(s.strip().rstrip("%"))
    except ValueError:
        return None


def _pair(s):
    if not s or "/" not in s:
        return (None, None)
    a, b = s.split("/", 1)
    return (_bytes(a), _bytes(b))


def _int(s):
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return None


def _run(args):
    # raise on a nonzero exit so a DOWN daemon (empty stdout, error on stderr) is distinguishable
    # from a genuinely empty result — otherwise "daemon unreachable" reads as "zero containers".
    r = subprocess.run([DOCKER, *args], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "docker command failed").strip()[:200])
    return [json.loads(line) for line in r.stdout.strip().splitlines() if line.strip()]


def main():
    if not DOCKER:
        print(json.dumps({"docker": {"error": "docker.exe not found (is Docker Desktop installed?)"}}))
        return
    try:
        try:
            ps = _run(["ps", "--all", "--format", "{{json .}}"])
        except Exception as e:
            # daemon down / unreachable — an explicit state, NOT zero containers
            print(json.dumps({"docker": {"daemon_ok": False, "error": str(e)[:200]}}))
            return
        try:
            stats = {s.get("Name"): s for s in _run(["stats", "--no-stream", "--format", "{{json .}}"])}
        except Exception:
            stats = {}
        containers = []
        for r in ps:
            st = stats.get(r.get("Names"), {})
            mem_used, mem_limit = _pair(st.get("MemUsage"))
            net_rx, net_tx = _pair(st.get("NetIO"))
            blk_r, blk_w = _pair(st.get("BlockIO"))
            containers.append({
                "name": r.get("Names"),
                "image": r.get("Image"),
                "status": r.get("Status"),
                "ports": r.get("Ports") or "",
                "cpu_pct": _pct(st.get("CPUPerc")),
                "mem_used_bytes": mem_used,
                "mem_limit_bytes": mem_limit,
                "mem_pct": _pct(st.get("MemPerc")),
                "net_rx_bytes": net_rx,
                "net_tx_bytes": net_tx,
                "blk_read_bytes": blk_r,
                "blk_write_bytes": blk_w,
                "pids": _int(st.get("PIDs")),
            })
        def _status(r):
            return str(r.get("Status", ""))
        running = sum(1 for r in ps if _status(r).startswith("Up"))
        # parse the status string for the states rules.py acts on. Docker writes these verbatim:
        #   "Up 2 hours (unhealthy)", "Restarting (1) 5 seconds ago", "Exited (0) 3 days ago",
        #   "Up 2 hours (Paused)".
        restarting = sum(1 for r in ps if _status(r).startswith("Restarting"))
        unhealthy = sum(1 for r in ps if "(unhealthy)" in _status(r))
        exited = sum(1 for r in ps if _status(r).startswith("Exited"))
        paused = sum(1 for r in ps if "(Paused)" in _status(r))
        print(json.dumps({"docker": {"daemon_ok": True, "running": running, "total": len(containers),
                                     "restarting": restarting, "unhealthy": unhealthy,
                                     "exited": exited, "paused": paused,
                                     "containers": containers}}))
    except Exception as e:
        print(json.dumps({"docker": {"error": str(e)}}))


def demo():  # parser self-check: python docker.py --test
    assert _bytes("120MiB") == 125829120
    assert _bytes("1.2kB") == 1200
    assert _bytes("0B") == 0
    assert _pct("0.15%") == 0.15
    assert _pair("120MiB / 7.6GiB") == (125829120, int(7.6 * 1024**3))
    assert _int("12") == 12 and _int(None) is None
    print("docker parsers ok")


if __name__ == "__main__":
    (demo if "--test" in sys.argv else main)()
