import json, re, urllib.request
LHM_URL = "http://127.0.0.1:8085/data.json"
def walk(node, temps, fans):
    name, val = node.get("Text", ""), node.get("Value", "")
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*(\S+)?", val) if val else None
    if m:
        unit = (m.group(2) or "")
        if unit.endswith("C"):
            temps.append((name, float(m.group(1))))
        elif unit == "RPM":
            fans[name] = int(float(m.group(1)))
    for ch in node.get("Children", []):
        walk(ch, temps, fans)
try:
    with urllib.request.urlopen(LHM_URL, timeout=3) as r:
        raw = json.loads(r.read().decode("utf-8", "replace"))
    temps, fans = [], {}
    walk(raw, temps, fans)
    pkg = [v for n, v in temps if "cpu" in n.lower() and "package" in n.lower()]
    cpu = pkg or [v for n, v in temps if "cpu" in n.lower()]
    print(json.dumps({"sensors": {"cpu_temp": int(max(cpu)) if cpu else None, "fans": fans}}))
except Exception as e:
    print(json.dumps({"sensors": {"error": f"LHM not reachable: {e}"}}))