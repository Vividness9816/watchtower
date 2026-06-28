# collectors/k3s.py — k3s pod state from WSL, via `wsl k3s kubectl`. Degrades if unreachable.
# k3s runs inside WSL, so we shell into WSL to query it. The default runs the bundled kubectl
# as root so it can read /etc/rancher/k3s/k3s.yaml on a stock k3s install.
# ADJUST K3S_CMD if needed:
#   - kubeconfig already set for your WSL user:  ["wsl", "kubectl", "get", "pods", "-A", "-o", "json"]
#   - k3s lives in a non-default distro:          prepend ["wsl", "-d", "Ubuntu", ...]
import json, subprocess

K3S_CMD = ["wsl", "-u", "root", "k3s", "kubectl", "get", "pods", "-A", "-o", "json"]

def main():
    try:
        r = subprocess.run(K3S_CMD, capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            print(json.dumps({"k3s": {"error": (r.stderr or "kubectl failed").strip()[:200]}}))
            return
        items = json.loads(r.stdout).get("items", [])
        pods = [{"name": i.get("metadata", {}).get("name"),
                 "namespace": i.get("metadata", {}).get("namespace"),
                 "phase": i.get("status", {}).get("phase")} for i in items]
        running = sum(1 for p in pods if p["phase"] == "Running")
        print(json.dumps({"k3s": {"running": running, "total": len(pods), "pods": pods}}))
    except Exception as e:
        print(json.dumps({"k3s": {"error": str(e)}}))

if __name__ == "__main__":
    main()