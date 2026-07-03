# checker.py — DETERMINISTIC E1 scorer. Given a contender's report TEXT and the gold findings for a
# snapshot, decide, per diagnosable component, what severity the report claims, then score status
# accuracy + finding precision/recall/F1 + hallucination. Applied identically to every contender.
#
# CONTRACT (published to all contenders — this lexicon is NOT incumbent-specific): a report names an
# abnormal component with a clear severity word (critical/severe/overheating  OR  warning/elevated/
# high/warm) and may affirm others nominal. Only the FIVE diagnosable components below are scored;
# commentary on non-thresholded readings (gpu power/util/vram, cpu load) is ignored, not penalized.
# Negated problems ("not overheating", "well below the critical limit") count as nominal.
import re
import gold

# component kind -> regex that names it. cpu/gpu also require a THERMAL indicator (below) so that
# "gpu power is high" / "cpu load high" are NOT mistaken for a temperature finding (audit F5).
_KIND = {
    "cpu_temp": (re.compile(r"\bcpu\b|\bprocessor\b", re.I), True),
    "gpu_temp": (re.compile(r"\bgpu\b|graphics card|\bvideo card\b", re.I), True),
    "mem":      (re.compile(r"\bram\b|\bmemory\b|\bmem\b", re.I), False),
    "disk":     (re.compile(r"\bdisk\b|\bstorage\b|\bdrive\b|\bc:\b|\bvolume\b", re.I), False),
    "whea":     (re.compile(r"\bwhea\b|hardware error|machine[- ]check|\bmce\b|\bmca\b", re.I), False),
}
_THERMAL = re.compile(r"\btemp\w*|\bthermal|\bhot\b|overheat\w*|°|degrees?|\b\d{2,3}\s*c\b|celsius|"
                      r"throttl\w*|\bcooling\b|\bfans?\b", re.I)
# severity lexicons — broad synonym coverage so a challenger's wording isn't penalized (audit F3)
_CRIT = re.compile(r"\b(critical|crit|severe(ly)?|dangerous(ly)?|danger|emergency|overheat\w*|"
                   r"too hot|in the red|maxed? ?out|thermal throttl\w*|failing|on fire)\b", re.I)
_WARN = re.compile(r"\b(warning|warn|elevated|elevate|caution|attention|heads[- ]?up|running warm|"
                   r"\bwarm\b|\bhigh\b|getting hot|approaching|near(ing)? (the )?limit|borderline|"
                   r"climbing|spiking|under pressure|low on|filling up|almost full|nearly full)\b", re.I)
_OK = re.compile(r"\b(nominal|healthy|normal|fine|ok|okay|no action|all systems|all clear|clean|"
                 r"no issues?|within (normal|limits?|range|spec)|safe range|below .{0,20}limit|"
                 r"plenty|nothing wrong|operating normally)\b", re.I)
_NEG = re.compile(r"\b(no|not|n't|never|without|below|within|under|nothing|free of|clear of|"
                  r"isn'?t|aren'?t|doesn'?t|don'?t|well under)\b", re.I)

_RANK = {"OK": 0, "WARN": 1, "CRIT": 2}


def _clauses(text: str) -> list[str]:
    # split on sentence enders AND commas so a severity word binds to the component in its own clause
    return [c for c in re.split(r"[.,\n;:!?]+", text) if c.strip()]


def _clause_sev(clause: str) -> "str | None":
    """Strongest NON-negated severity asserted in a clause, or None. Negated problem -> OK."""
    crit, warn, ok = _CRIT.search(clause), _WARN.search(clause), _OK.search(clause)
    negated = bool(_NEG.search(clause))
    if (crit or warn) and not negated:
        return "CRIT" if crit else "WARN"
    if ok or ((crit or warn) and negated):
        return "OK"
    return None


def claimed_severities(report: str) -> dict[str, str]:
    """Per diagnosable component, the STRONGEST severity the report asserts: CRIT/WARN/OK (or absent).
    WHEA is special: naming a hardware error (non-negated) asserts a CRITICAL problem even with no
    explicit severity adjective ('WHEA hardware errors: 3' is a finding, not a neutral mention)."""
    claimed: dict[str, str] = {}
    for clause in _clauses(report):
        sev = _clause_sev(clause)
        negated = bool(_NEG.search(clause))
        thermal = bool(_THERMAL.search(clause))
        for kind, (rx, needs_thermal) in _KIND.items():
            if not rx.search(clause):
                continue
            if needs_thermal and not thermal:
                continue                      # "gpu power high" is not a gpu-temp claim
            k_sev = sev
            if kind == "whea" and k_sev is None and not negated:
                k_sev = "CRIT"
            if k_sev is None:
                continue
            if _RANK[k_sev] > _RANK.get(claimed.get(kind, "_"), -1):
                claimed[kind] = k_sev
    return claimed


def claimed_status(report: str) -> str:
    """Overall status asserted: strongest of any per-component claim (incl. WHEA-by-presence) and any
    bare status phrase (e.g. 'all nominal')."""
    best = None
    for s in claimed_severities(report).values():
        if best is None or _RANK[s] > _RANK[best]:
            best = s
    for clause in _clauses(report):
        s = _clause_sev(clause)
        if s and (best is None or _RANK[s] > _RANK[best]):
            best = s
    return {"CRIT": "CRITICAL", "WARN": "WARNING", "OK": "OK", None: "UNKNOWN"}[best]


def score_one(report: str, findings: list[dict]) -> dict:
    gold_sev: dict[str, str] = {}
    for f in findings:
        k = gold.kind_of(f["what"])
        if _RANK[f["level"]] > _RANK.get(gold_sev.get(k, "_"), -1):
            gold_sev[k] = f["level"]
    claimed = claimed_severities(report)
    claimed_problem = {k for k, s in claimed.items() if s in ("WARN", "CRIT")}
    gold_problem = set(gold_sev)

    tp = len(gold_problem & claimed_problem)
    fn = len(gold_problem - claimed_problem)
    fp = len(claimed_problem - gold_problem)
    sev_match = sum(1 for k in (gold_problem & claimed_problem) if claimed[k] == gold_sev[k])
    return {"status_ok": int(claimed_status(report) == gold.status_of(findings)),
            "tp": tp, "fp": fp, "fn": fn, "sev_match": sev_match,
            "n_gold": len(gold_problem), "n_flagged": len(claimed_problem)}


def aggregate(per: list[dict]) -> dict:
    TP = sum(p["tp"] for p in per); FP = sum(p["fp"] for p in per); FN = sum(p["fn"] for p in per)
    prec = TP / (TP + FP) if (TP + FP) else 1.0
    rec = TP / (TP + FN) if (TP + FN) else 1.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    flagged = sum(p["n_flagged"] for p in per)
    return {"status_acc": sum(p["status_ok"] for p in per) / len(per),
            "precision": prec, "recall": rec, "f1": f1,
            "severity_acc": sum(p["sev_match"] for p in per) / TP if TP else 1.0,   # diagnostic
            "halluc_rate": FP / flagged if flagged else 0.0,
            "halluc_per_report": FP / len(per), "n": len(per)}


def demo():
    snap = {"gpu": {"temp": 99, "power": 560, "util": 80, "vram_pct": 50}, "disk": {"C": 90},
            "sensors": {"cpu_temp": 45}, "mem": {"pct": 40}, "whea": {"recent_errors": 0}, "cpu": {"load": 95}}
    f = gold.diagnose(snap)                       # gold: gpu_temp CRIT, disk WARN
    good = "Something is in the red. GPU temp is critical at 99C. Disk C is filling up at 90%."
    alt  = "The graphics card is overheating and the C: volume is almost full; CPU and RAM look fine."
    neg  = "GPU is not overheating, well below the critical 88C limit. All systems nominal."  # wrong: misses both
    f5   = "GPU power is high at 560W and CPU load is high at 95%. GPU temp critical 99C. Disk almost full."
    sg, sa = score_one(good, f), score_one(alt, f)
    sn, s5 = score_one(neg, f), score_one(f5, f)
    assert sg["tp"] == 2 and sg["fp"] == 0 and sg["status_ok"], sg
    assert sa["tp"] == 2 and sa["fp"] == 0, ("alt phrasing must score", sa)      # F3
    assert sn["tp"] == 0 and sn["fp"] == 0, ("negation -> no false flags", sn)   # F4
    assert s5["fp"] == 0 and s5["tp"] == 2, ("power/load not a temp halluc", s5) # F5
    # WHEA by presence: 'WHEA hardware errors: 3' has no severity adjective but IS a critical finding
    wsnap = {"whea": {"recent_errors": 3}, "sensors": {"cpu_temp": 45}, "gpu": {"temp": 50},
             "mem": {"pct": 40}, "disk": {"C": 50}, "cpu": {"load": 10}}
    wf = gold.diagnose(wsnap)
    wrep = score_one("CRITICAL: Something is wrong. WHEA hardware errors: 3.", wf)
    wneg = score_one("All systems nominal. No hardware errors detected.", wf)
    assert wrep["tp"] == 1 and wrep["status_ok"], ("whea by presence", wrep)
    assert wneg["tp"] == 0 and wneg["fp"] == 0, ("no hardware errors -> no flag", wneg)
    print("checker ok:", {k: round(v, 3) for k, v in aggregate([sg, sa, sn, s5, wrep]).items() if isinstance(v, float)})


if __name__ == "__main__":
    demo()
