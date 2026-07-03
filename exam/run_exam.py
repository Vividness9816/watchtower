# run_exam.py — the FROZEN system exam. Scores the whole Watch Tower stack 0..1 on seven
# dimensions. Built once at RSI run 0 and never edited afterwards (the freeze commit hash is
# recorded in exam/FROZEN.md); every RSI run must beat the previous composite to count.
#
#   python exam/run_exam.py --run 0                # full official score (needs Ollama up)
#   python exam/run_exam.py --only s3,s6           # dev: subset (composite omitted)
#
# Dimensions (weights sum to 1.0):
#   S1 coverage   .15  fraction of the frozen "reportable universe" present in a live snapshot
#   S2 rules      .15  frozen golden suite against rules.diagnose (behavior + robustness)
#   S3 narration  .20  tiny-GPT reports on 200 held-out snapshots vs frozen gold (F1/status/halluc)
#   S4 retrieval  .10  MRR@5 of rag.py over 33 frozen QA pairs (word-overlap hit rule)
#   S5 brain      .15  Ollama chat on 12 frozen contexts, deterministic assertions (seed 7, temp 0)
#   S6 dataflow   .10  latency budgets, live ring, history round-trip, ingest loopback, ship config
#   S7 features   .15  search API, notes API, graph data paths (headroom by design at run 0)
import argparse, hashlib, importlib, json, pathlib, re, subprocess, sys, time, urllib.request

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

import gold, checker  # frozen ground truth + deterministic narration scorer  # noqa: E402

W = {"s1": 0.15, "s2": 0.15, "s3": 0.20, "s4": 0.10, "s5": 0.15, "s6": 0.10, "s7": 0.15}
PY = sys.executable
OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"


def _load(name):
    p = HERE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ---------------------------------------------------------------- S1: coverage
def s1_coverage(detail):
    uni = _load("universe.json")
    if uni is None:
        return None
    import sysdiag
    snap = sysdiag.snapshot()

    def dig(path):
        cur = snap
        for k in path:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    hit, miss = [], []
    for item in uni:
        v = dig(item["path"])
        ok = v is not None and not (isinstance(v, dict) and "error" in v)
        (hit if ok else miss).append(item["family"])
    detail["s1"] = {"present": len(hit), "total": len(uni), "missing": miss}
    return len(hit) / len(uni)


# ---------------------------------------------------------------- S2: rules golden suite
def s2_rules(detail):
    cases = _load("cases_rules.json")
    if cases is None:
        return None
    import rules
    passed, failures = 0, []
    for c in cases:
        try:
            got = rules.diagnose(c["snap"])
        except Exception as e:
            failures.append(f"{c['name']}: CRASHED {e}")
            continue
        ok = True
        for exp in c.get("expect", []):
            if not any(f["level"] == exp["level"] and exp["what_contains"].lower() in f["what"].lower()
                       for f in got):
                ok = False
                failures.append(f"{c['name']}: missing {exp['level']} ~'{exp['what_contains']}'")
        for forb in c.get("forbid", []):
            if any(forb.lower() in f["what"].lower() for f in got):
                ok = False
                failures.append(f"{c['name']}: forbidden finding ~'{forb}' fired")
        passed += ok
    detail["s2"] = {"passed": passed, "total": len(cases), "failures": failures[:20]}
    return passed / len(cases)


# ---------------------------------------------------------------- S3: narration (tiny GPT)
def s3_narration(detail, n=200):
    import torch
    import infer
    bundle = infer.load(str(REPO / "ckpt.pt"), str(REPO / "vocab.json"))
    per = []
    t0 = time.time()
    for i in range(n):
        import random
        snap = gold.synthetic_snapshot(random.Random(10_000 + i))   # held-out: train used Random(1337)
        findings = gold.diagnose(snap)
        torch.manual_seed(31_337 + i)                               # deterministic sampling
        rpt = infer.generate_report(bundle, gold.serialize_metrics(snap))
        per.append(checker.score_one(rpt, findings))
    agg = checker.aggregate(per)
    agg["latency_ms"] = round((time.time() - t0) * 1000 / n, 1)
    detail["s3"] = agg
    return round(0.6 * agg["f1"] + 0.3 * agg["status_acc"] + 0.1 * (1 - agg["halluc_rate"]), 4)


# ---------------------------------------------------------------- S4: retrieval (rag.py)
E2_HIT = 0.7


def s4_retrieval(detail, k=5):
    cases = _load("cases_retrieval.json")
    import rag
    con = rag.build_index()
    rr, hits, detail_rows = 0.0, 0, []
    for it in cases:
        got = rag._knn(con, it["question"], k)
        span_words = set(re.sub(r"\s+", " ", it["answer_span"]).strip().lower().split())
        rank = 0
        for i, (score, src, txt) in enumerate(got, 1):
            cw = set(re.sub(r"\s+", " ", txt).strip().lower().split())
            if len(span_words & cw) / max(1, len(span_words)) >= E2_HIT:
                rank = i
                break
        if rank:
            hits += 1
            rr += 1.0 / rank
        detail_rows.append({"q": it["question"][:60], "rank": rank})
    con.close()
    n = len(cases)
    detail["s4"] = {"mrr": round(rr / n, 4), "hit_at_k": round(hits / n, 4), "k": k, "n": n,
                    "misses": [d["q"] for d in detail_rows if not d["rank"]][:10]}
    return round(rr / n, 4)


# ---------------------------------------------------------------- S5: brain (Ollama, frozen contexts)
def s5_brain(detail):
    import brain
    cases = _load("cases_brain.json")
    results, total, got_points = [], 0, 0
    for c in cases:
        msgs = [{"role": "system", "content": brain.SYSTEM.format(ctx=c["context"])},
                {"role": "user", "content": c["question"]}]
        body = json.dumps({"model": brain.MODEL, "messages": msgs, "stream": False,
                           "keep_alive": "30m",
                           "options": {"temperature": 0.0, "seed": 7, "num_ctx": 32768}}).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                ans = json.loads(r.read())["message"]["content"]
        except Exception as e:
            results.append({"name": c["name"], "error": str(e), "score": 0.0})
            total += 1
            continue
        checks, ok = [], 0
        for rx in c["must"]:
            hit = bool(re.search(rx, ans, re.I))
            checks.append(("must", rx, hit))
        for rx in c["must_not"]:
            hit = not re.search(rx, ans, re.I | re.M)
            checks.append(("must_not", rx, hit))
        if c["any_of"]:
            hit = any(re.search(rx, ans, re.I) for rx in c["any_of"])
            checks.append(("any_of", "|".join(c["any_of"])[:60], hit))
        ok = sum(1 for _, _, h in checks if h)
        total += len(checks)
        got_points += ok
        results.append({"name": c["name"], "passed": ok, "of": len(checks),
                        "failed": [f"{k}:{rx}" for k, rx, h in checks if not h],
                        "answer_head": ans[:200]})
    detail["s5"] = {"cases": results, "points": got_points, "total": total}
    return round(got_points / total, 4) if total else 0.0


# ---------------------------------------------------------------- S6: dataflow
def s6_dataflow(detail):
    checks = {}

    def run_py(args, timeout=120, env=None):
        import os
        e = {**os.environ, **(env or {})}
        return subprocess.run([PY, *args], capture_output=True, text=True,
                              timeout=timeout, cwd=str(REPO), env=e)

    # 1-2: pure-logic self-tests
    checks["schema_demo"] = "schema ok" in run_py(["schema.py"]).stdout
    checks["rules_demo"] = "rules ok" in run_py(["rules.py"]).stdout
    # 3: live ring demo (multi-host isolation + local sampler)
    checks["live_demo"] = "live ok" in run_py(["live.py"], timeout=90).stdout
    # 4: fast-tier latency budget
    t0 = time.time()
    import sysdiag
    fast = sysdiag.snapshot(only=["cpu", "gpu", "mem", "sensors", "disk"])
    fast_s = time.time() - t0
    checks["fast_tier_under_5s"] = fast_s < 5.0 and len(fast) >= 4
    # 5: full-fleet latency budget
    t0 = time.time()
    full = sysdiag.snapshot()
    full_s = time.time() - t0
    checks["full_fleet_under_30s"] = full_s < 30.0
    checks["full_fleet_low_errors"] = len(full.get("_errors", [])) <= 2
    # 6: HERMETIC history round-trip — history.py and trends.py must honor
    # WATCHTOWER_HISTORY_DB so the exam never mutates the real history.db
    import tempfile
    tmpdb = str(pathlib.Path(tempfile.mkdtemp()) / "exam_history.db")
    r = run_py(["history.py"], env={"WATCHTOWER_HISTORY_DB": tmpdb})
    checks["history_write_hermetic"] = "logged" in r.stdout and pathlib.Path(tmpdb).exists()
    r = run_py(["-c", "import trends; df = trends.series('CPU temp (C)', 'Last 10 runs'); "
                "print('trends-ok' if len(df) >= 1 and list(df.columns) == ['time', 'value', 'when'] else 'trends-bad', len(df))"],
               env={"WATCHTOWER_HISTORY_DB": tmpdb})
    checks["trends_read_hermetic"] = "trends-ok" in r.stdout
    # 6b: UI-render robustness — hostile remote snapshots must not crash the panel path
    r = run_py(["exam/_ui_robustness.py"], timeout=60)
    checks["ui_render_robust"] = "ui robust ok" in r.stdout
    # 6c: live.deltas() digest correctness (this text feeds the LLM's TRENDS block)
    r = run_py(["-c",
                "import live, time\n"
                "now = time.time()\n"
                "st = live._new_host()\n"
                "for i, v in enumerate([45, 48, 50, 52]):\n"
                "    st['buf'].append((now - 60 + i * 15, {'CPU temp (C)': v}))\n"
                "live._hosts['EXAM'] = st\n"
                "d = live.deltas(host='EXAM')\n"
                "print('deltas-ok' if '45 -> 52' in d and 'min 45' in d and 'max 52' in d and 'n=4' in d else 'deltas-bad', repr(d))"])
    checks["deltas_correct"] = "deltas-ok" in r.stdout
    # 6d: exit-code contract — sysdiag exit code must be consistent with its findings
    #     (0 = no findings, 1 = WARN only, 2 = CRIT present)
    r = run_py(["-c",
                "import sysdiag\n"
                "ec = getattr(sysdiag, 'exit_code_for', None)\n"
                "print('exitfn-ok' if ec and ec([]) == 0 and ec([{'level': 'WARN'}]) == 1 "
                "and ec([{'level': 'WARN'}, {'level': 'CRIT'}]) == 2 else 'exitfn-missing')"])
    checks["exit_code_contract"] = "exitfn-ok" in r.stdout
    # 7: ingest loopback — auth, caps, per-host ring (fresh interpreter so live.py state is clean)
    loop = run_py(["exam/_ingest_loopback.py"], timeout=60,
                  env={"WATCHTOWER_TOKEN": "exam-secret", "WATCHTOWER_REMOTE": "1"})
    checks["ingest_loopback"] = "ingest ok" in loop.stdout
    if "ingest ok" not in loop.stdout:
        detail.setdefault("s6_errors", []).append(loop.stdout[-500:] + loop.stderr[-500:])
    # 8: ship config precedence (env beats file)
    prec = run_py(["-c", "import ship; print(ship.load_config()['host'])"],
                  env={"WATCHTOWER_HOST": "exam-host-override"})
    checks["ship_env_precedence"] = prec.stdout.strip().endswith("exam-host-override")
    detail["s6"] = {"checks": checks, "fast_s": round(fast_s, 2), "full_s": round(full_s, 2)}
    return sum(checks.values()) / len(checks)


# ---------------------------------------------------------------- S7: features (headroom by design)
def s7_features(detail):
    checks = {}
    import socket
    local = socket.gethostname()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    # search API: by component, by computer, by date/time window
    try:
        import search
        importlib.reload(search)
        rows = search.search(component="cpu_temp")
        checks["search_by_component"] = (len(rows) >= 1 and
                                         all({"ts", "host", "metric", "value"} <= set(r) for r in rows[:5]))
        checks["search_by_host"] = (len(search.search(component="cpu_temp", host=local)) >= 1 and
                                    len(search.search(component="cpu_temp", host="__no_such_host__")) == 0)
        checks["search_by_time"] = (len(search.search(component="cpu_temp",
                                                      since="1970-01-01T00:00:00", until=now)) >= 1 and
                                    len(search.search(component="cpu_temp",
                                                      until="1970-01-02T00:00:00")) == 0)
        checks["search_free_text"] = isinstance(search.search(component="temp"), list)  # substring match
    except Exception:
        checks["search_by_component"] = checks["search_by_host"] = False
        checks["search_by_time"] = checks["search_free_text"] = False
    # notes API: multi-user, persistent, capped — HERMETIC via WATCHTOWER_NOTES_DB
    import os as _os, tempfile as _tf
    tmpnotes = str(pathlib.Path(_tf.mkdtemp()) / "exam_notes.db")
    nenv = {**_os.environ, "WATCHTOWER_NOTES_DB": tmpnotes}
    marker = f"exam-note-{int(time.time())}"

    def notes_py(code):
        return subprocess.run([PY, "-c", code], capture_output=True, text=True,
                              cwd=str(REPO), timeout=30, env=nenv).stdout.strip()

    try:
        out1 = notes_py(f"import notes\n"
                        f"notes.add_note('exam-user', '{marker}')\n"
                        f"ns = notes.list_notes()\n"
                        f"print(any(n.get('text') == '{marker}' and n.get('user') == 'exam-user' "
                        f"and n.get('ts') for n in ns))")
        checks["notes_add_list"] = out1.endswith("True")
        # persistence: a SECOND process (same env) must see the note — true SQLite persistence
        out2 = notes_py(f"import notes; print(any(n.get('text') == '{marker}' for n in notes.list_notes()))")
        checks["notes_persist"] = out2.endswith("True")
        out3 = notes_py("import notes\n"
                        "try:\n"
                        "    notes.add_note('exam-user', 'x' * 100_000)\n"
                        "except ValueError:\n"
                        "    pass\n"
                        "print(all(len(n.get('text', '')) <= 10_000 for n in notes.list_notes()))")
        checks["notes_capped"] = out3.endswith("True")
    except Exception:
        checks["notes_add_list"] = checks["notes_persist"] = checks["notes_capped"] = False
    # graphs: history + live data paths yield plottable frames
    try:
        import trends
        checks["graph_history"] = len(trends.series("CPU temp (C)", "Last 10 runs")) >= 1
    except Exception:
        checks["graph_history"] = False
    try:
        r = subprocess.run([PY, "exam/_graph_live.py"], capture_output=True, text=True,
                           cwd=str(REPO), timeout=90)
        checks["graph_live"] = "graph live ok" in r.stdout
    except Exception:
        checks["graph_live"] = False
    detail["s7"] = {"checks": checks}
    return sum(checks.values()) / len(checks)


# ---------------------------------------------------------------- freeze integrity
FROZEN_FILES = ["run_exam.py", "gold.py", "checker.py", "universe.json", "cases_rules.json",
                "cases_retrieval.json", "cases_brain.json", "_ingest_loopback.py",
                "_graph_live.py", "_ui_robustness.py"]


def verify_frozen() -> bool:
    """True iff every exam file matches the SHA256 manifest written at freeze time."""
    mf = HERE / "freeze_manifest.json"
    if not mf.exists():
        return False
    want = json.loads(mf.read_text(encoding="utf-8"))
    for name in FROZEN_FILES:
        got = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if want.get(name) != got:
            print(f"!! FROZEN-EXAM DRIFT: {name} does not match the freeze manifest", file=sys.stderr)
            return False
    return True


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, default=-1, help="RSI run number (for the results file)")
    ap.add_argument("--only", default="", help="comma subset e.g. s3,s6 (composite omitted)")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    fns = {"s1": s1_coverage, "s2": s2_rules, "s3": s3_narration, "s4": s4_retrieval,
           "s5": s5_brain, "s6": s6_dataflow, "s7": s7_features}
    detail, scores = {}, {}
    for name, fn in fns.items():
        if only and name not in only:
            continue
        t0 = time.time()
        try:
            scores[name] = fn(detail)
        except Exception as e:
            import traceback
            scores[name] = 0.0
            detail[f"{name}_crash"] = traceback.format_exc()[-800:]
            print(f"  {name} CRASHED: {e}", file=sys.stderr)
        print(f"  {name}: {scores[name] if scores[name] is None else round(scores[name], 4)}"
              f"  ({time.time() - t0:.1f}s)", flush=True)
    ran_all = set(scores) == set(fns) and all(v is not None for v in scores.values())
    composite = round(sum(W[k] * v for k, v in scores.items()), 4) if ran_all else None
    out = {"run": args.run, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "frozen_ok": verify_frozen(),
           "scores": {k: (None if v is None else round(v, 4)) for k, v in scores.items()},
           "composite": composite, "detail": detail}
    resdir = HERE / "results"
    resdir.mkdir(exist_ok=True)
    tag = f"run-{args.run}" if args.run >= 0 else f"dev-{int(time.time())}"
    (resdir / f"{tag}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"run": args.run, "scores": out["scores"], "composite": composite}, indent=1))


if __name__ == "__main__":
    main()
