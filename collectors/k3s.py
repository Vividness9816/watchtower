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
        pods = []
        crashloop = not_ready = 0
        for i in items:
            st = i.get("status", {}) or {}
            cs = st.get("containerStatuses") or []
            # phase stays 'Running' through a CrashLoopBackOff (k8s semantics), so judge the
            # container states directly, not just the pod phase.
            waiting = [c.get("state", {}).get("waiting", {}).get("reason")
                       for c in cs if isinstance(c, dict)]
            pod_crashloop = any(w == "CrashLoopBackOff" for w in waiting)
            pod_notready = bool(cs) and any(not c.get("ready", False) for c in cs
                                            if isinstance(c, dict)) and st.get("phase") == "Running"
            restarts = sum(int(c.get("restartCount") or 0) for c in cs if isinstance(c, dict))
            crashloop += pod_crashloop
            not_ready += pod_notready and not pod_crashloop
            pods.append({"name": i.get("metadata", {}).get("name"),
                         "namespace": i.get("metadata", {}).get("namespace"),
                         "phase": st.get("phase"), "restarts": restarts,
                         "crashloop": pod_crashloop})
        running = sum(1 for p in pods if p["phase"] == "Running")
        print(json.dumps({"k3s": {"running": running, "total": len(pods),
                                  "crashloop": crashloop, "not_ready": not_ready, "pods": pods}}))
    except Exception as e:
        print(json.dumps({"k3s": {"error": str(e)}}))

if __name__ == "__main__":
    main()