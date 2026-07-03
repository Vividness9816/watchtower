# Security — scanner sweep & triage

Watch Tower is a **local, read-only diagnostics tool**: it spawns fixed read-only commands
(PowerShell/CIM, `nvidia-smi`, `docker`, `smartctl`, …), renders their output, and talks to a
local Ollama. Spawning subprocesses and parsing their output is the product, not an accident —
that shapes the triage below. Threat model: the exposed surfaces are the Gradio UI on
`127.0.0.1:7860` (notes = untrusted browser input), the optional remote-mode `/ingest` listener
(token-gated, semi-trusted JSON from monitored machines), and the operator-trusted config files
(`ship.config.json`, `ssh.config.json`).

**Sweep of 2026-07-03** (full scanner pass on top of the earlier manual red-team + hardening —
see `test_security.py` for the regression guards from that pass):

| Scanner | Scope | Result |
|---|---|---|
| gitleaks 8.30.1 | full git history (49 commits) + working tree | **no leaks** |
| pip-audit (`-r requirements.txt`, latest resolution) | the 4 pip deps | **0 known vulns** |
| pip-audit (running venv freeze) | actual installed versions | 2 hits, triaged below |
| bandit 1.9.4 | app (96), collectors (74), tests (32) | all triaged below, 1 fix |
| semgrep `p/python` + `p/security-audit` | whole repo minus `exam/` | 5 hits, all triaged below |

## Fixed

- **`infer.py` `torch.load` without `weights_only`** (bandit B614). The checkpoint is tensors +
  a plain config dict, so full-pickle execution is never needed. Now explicit
  `weights_only=True`: on torch ≥2.6 this was already the default; on the older torch the README
  still permits (≥2.0), loading a ckpt.pt from anywhere else was arbitrary code execution.
  Verified: `python infer.py --demo` loads and narrates unchanged.
- **Local venv `setuptools` 70.2.0 → 82.x** (PYSEC-2025-49, path traversal in `PackageIndex`,
  fixed in 78.1.1). Not reachable through Watch Tower (nothing imports setuptools at runtime),
  but the venv upgrade is free. Fresh venvs built per the recreate guides get a current
  setuptools anyway.

## Triaged — no action

- **torch CVE-2025-3000** (`torch.jit.script` memory corruption, "local" vector, no fixed
  release listed). Watch Tower never uses TorchScript — the only torch entry points are eager
  `GPT` forward/generate and the now-`weights_only` `torch.load`. Exploitation requires running
  attacker-supplied Python locally, which is already code execution. Not reachable.
- **bandit B404/B603/B607 (~55×, subprocess use / partial paths)** — the collector fleet by
  design. Every argv is a fixed list; no `shell=True` anywhere; nothing user-supplied enters an
  argv. The two config-driven cases are operator-trusted by definition: `ssh.py` runs read-only
  checks the operator wrote in `ssh.config.json` (key-auth, `BatchMode`), and `ship.py` POSTs to
  the operator's own ingest URL. Partial paths (`powershell`, `nvidia-smi`, `ollama`, …) are
  deliberate PATH resolution so installs in nonstandard prefixes work.
- **bandit B608 (3×, search.py "SQL injection")** — false positive. The f-string assembles the
  WHERE clause from a fixed set of literal fragments (`"host = ?"`, `"ts >= ?"`); every value is
  a bound parameter. No user text ever reaches SQL syntax.
- **bandit B310 + semgrep `dynamic-urllib-use` (5×: brain.py:60, rag.py:74/85,
  collectors/sensors.py:64, ship.py:71)** — audited each: brain/rag/sensors open hardcoded
  `http://127.0.0.1` URLs (Ollama, LibreHardwareMonitor); ship.py opens the operator-configured
  ingest URL, which is the product's function. No user-supplied URL, no `file:`/custom-scheme
  reachability.
- **bandit B101 (100×, asserts)** — the repo's deliberate self-test style (`demo()` +
  `__main__` blocks) plus test files; the four asserts in import-time/production paths
  (gpt.py construction/forward internal invariants, context.py/trends.py `__main__` checks)
  guard no trust boundary. Nothing runs under `python -O`; the trust-boundary checks that
  matter (notes length/emptiness, ingest token/size/type) raise real exceptions, not asserts.
- **bandit B110/B112 (try/except pass/continue)** — the documented degrade-don't-crash rule for
  collector/pipeline hot paths (a failing sensor must never kill the sampler loop).
- **bandit B311 (`random`, 4×)** — synthetic training-corpus generation and sampling jitter;
  nothing security-relevant derives from these PRNGs.
- **bandit B605 (art.py `os.system("")`)** — empty-string call that flips the legacy Windows
  console into ANSI mode; executes nothing.
- **bandit B102 (`exec` in tests/test_linux_parsers.py)** — deliberately execs the
  repo's own embedded Linux-collector source constants against fixtures; input is
  repo-controlled by construction.

## Standing posture

- UI binds `127.0.0.1` only; remote `/ingest` refuses to start without `WATCHTOWER_TOKEN`
  (constant-time compare), caps payloads at 2 MB, caps distinct hosts at 256, and treats
  payload fields as untrusted (escaped before rendering — `test_security.py`).
- LLM output is advisory text only, never executed; the model runs locally.
- Secrets: none in the repo (gitleaks-clean history); configs holding anything private
  (`*.config.json`) are gitignored, with `.example` templates tracked.
- Re-run the sweep after any change touching a trust boundary:
  `python -m bandit -r . -x ./exam,./collectors,./tests` (collectors/tests separately),
  `gitleaks git .`, `python -m pip_audit -r requirements.txt`, semgrep via Docker.
