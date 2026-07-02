# collectors/net.py — ping 1.1.1.1 (stdlib) + link state + NIC error/discard counters
# (Get-NetAdapterStatistics) + DNS resolve time (stdlib; catches a dead/slow Pi-hole
# even when raw IP ping is fine — the classic "internet up but nothing loads").
import json, subprocess, re, platform, socket, time


def ping(host="1.1.1.1"):
    n = "-n" if platform.system() == "Windows" else "-c"
    try:
        out = subprocess.run(["ping", n, "1", host], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"time[=<]\s*(\d+)\s*ms", out)   # "time=12ms" / "time<1ms"
        return int(m.group(1)) if m else None
    except Exception:
        return None


def dns_ms(name="example.com"):
    t0 = time.perf_counter()
    try:
        socket.getaddrinfo(name, 443)
        return int((time.perf_counter() - t0) * 1000)
    except OSError:
        return None                                   # resolution failing IS the signal


# first resolve exercises the cold path (Pi-hole -> upstream), second the cache;
# a slow cold hit is normal-ish, a slow SECOND hit means the resolver itself is sick
dns_cold, dns_warm = dns_ms(), dns_ms()


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


lk = link() or {}
print(json.dumps({"net": {"ping_ms": ping(), "target": "1.1.1.1",
                          "dns_ms": dns_warm, "dns_cold_ms": dns_cold,
                          "up": bool(lk.get("Name")), "name": lk.get("Name"),
                          "speed": lk.get("LinkSpeed"),
                          "rx_errors": lk.get("RxErr"), "tx_errors": lk.get("TxErr"),
                          "rx_discards": lk.get("RxDisc"), "tx_discards": lk.get("TxDisc")}}))
