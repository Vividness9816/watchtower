# collectors/net.py — ping 1.1.1.1 (stdlib) + link state + NIC error/discard counters
# (Get-NetAdapterStatistics) + DNS resolve time (stdlib; catches a dead/slow Pi-hole
# even when raw IP ping is fine — the classic "internet up but nothing loads").
import json, subprocess, re, platform, socket, time, threading


def ping(host="1.1.1.1"):
    n = "-n" if platform.system() == "Windows" else "-c"
    try:
        out = subprocess.run(["ping", n, "1", host], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]\s*(\d+)\s*ms", out)   # "time=12ms" / "time<1ms"
        return int(m.group(1)) if m else None
    except Exception:
        return None


def dns_ms(name="example.com", wait=13.0):
    # getaddrinfo has no timeout knob and a dead resolver stalls it ~10-12s per call,
    # which would blow sysdiag's 25s kill switch — so bound it with a daemon thread.
    # wait=13 clears this LAN's measured worst legit cold resolve (~11s via Pi-hole).
    res = {}

    def _resolve():
        t0 = time.perf_counter()
        try:
            socket.getaddrinfo(name, 443)
            res["ms"] = int((time.perf_counter() - t0) * 1000)
        except OSError:
            res["ms"] = None                          # resolution failing IS the signal
    th = threading.Thread(target=_resolve, daemon=True)
    th.start()
    th.join(wait)
    return res.get("ms")                              # still running -> None (resolver sick)


def dns_pair():
    # cold exercises the resolver->upstream path, warm the cache; skip warm if cold hung
    cold = dns_ms()
    warm = dns_ms(wait=6.0) if cold is not None else None
    return cold, warm


def link():
    ps = (r"$a=Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | Select-Object -First 1;"
          r"$s=$a | Get-NetAdapterStatistics -EA SilentlyContinue;"
          r"[pscustomobject]@{Name=$a.Name;LinkSpeed=$a.LinkSpeed;"
          r"RxErr=$s.ReceivedPacketErrors;TxErr=$s.OutboundPacketErrors;"
          r"RxDisc=$s.ReceivedDiscardedPackets;TxDisc=$s.OutboundDiscardedPackets}"
          r"|ConvertTo-Json -Compress")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return json.loads(out) if out else None
    except Exception:
        return None


# run the three probes CONCURRENTLY so worst case is max(dns 19, link 10, ping 5) ~= 19s,
# safely under sysdiag's 25s kill switch even with the resolver fully dead
r = {}
probes = [threading.Thread(target=lambda: r.__setitem__("dns", dns_pair()), daemon=True),
          threading.Thread(target=lambda: r.__setitem__("lk", link()), daemon=True),
          threading.Thread(target=lambda: r.__setitem__("ping", ping()), daemon=True)]
for t in probes:
    t.start()
for t in probes:
    t.join(21)
dns_cold, dns_warm = r.get("dns") or (None, None)
lk = r.get("lk") or {}
print(json.dumps({"net": {"ping_ms": r.get("ping"), "target": "1.1.1.1",
                          "dns_ms": dns_warm, "dns_cold_ms": dns_cold,
                          "up": bool(lk.get("Name")), "name": lk.get("Name"),
                          "speed": lk.get("LinkSpeed"),
                          "rx_errors": lk.get("RxErr"), "tx_errors": lk.get("TxErr"),
                          "rx_discards": lk.get("RxDisc"), "tx_discards": lk.get("TxDisc")}}))
