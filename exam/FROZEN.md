# The Frozen Exam — Watch Tower RSI

This directory is the **frozen system exam**. It scores the whole Watch Tower stack on a
0..1 scale across seven dimensions and is the referee for the RSI (recursive self-improvement)
loop: **every RSI run must beat the previous run's composite to count as an improvement.**

## Freeze contract

- Built once at **run 0** (baseline below) and **never edited afterwards**.
- `freeze_manifest.json` holds a SHA256 of every scored file. `run_exam.py`'s `verify_frozen()`
  recomputes those hashes each run and sets `frozen_ok`; a mismatch prints a loud drift warning.
  This is the meta-exam: a contender cannot quietly weaken the questions to inflate a score.
- `gold.py` is a **self-contained** copy of the run-0 schema + rules (snapshot generation, metric
  serialization, rule-based diagnosis). It never imports the live `schema.py`/`rules.py`, so no
  change to the product can move what "correct" means for S3.
- The exam is **hermetic**: history/notes round-trips go through `WATCHTOWER_HISTORY_DB` /
  `WATCHTOWER_NOTES_DB` temp files, so scoring never mutates the real `history.db`/`notes.db`.

## Dimensions (weights sum to 1.0)

| Dim | Weight | What it scores | Method (deterministic, no LLM-judge) |
|-----|--------|----------------|--------------------------------------|
| **S1 coverage** | .15 | fraction of the frozen "reportable universe" (`universe.json`, 78 families) present in a live snapshot | run `sysdiag.snapshot()`, count non-error families |
| **S2 rules** | .15 | `rules.diagnose` against a golden suite (`cases_rules.json`) | expect/forbid findings per frozen snapshot; robustness cases must not crash |
| **S3 narration** | .20 | tiny-GPT reports on 200 held-out snapshots (seeds 10000+, disjoint from training) | `checker.py` F1/status-acc/halluc vs `gold.diagnose`; sampling seeded (`31337+i`) |
| **S4 retrieval** | .10 | `rag.py` MRR@5 over 33 frozen QA pairs (`cases_retrieval.json`) | word-overlap hit rule (≥0.7 of the gold span's words in a retrieved chunk) |
| **S5 brain** | .15 | Ollama chat on 13 frozen contexts (`cases_brain.json`), incl. injection + absent-data canaries | deterministic regex assertions (seed 7, temp 0): must / must_not / any_of |
| **S6 dataflow** | .10 | latency budgets, live ring, hermetic history round-trip, ingest loopback, ship config, exit-code contract, deltas digest, UI-render robustness | 13 boolean checks |
| **S7 features** | .15 | search API (component/host/time), notes API (multi-user/persistent/capped), history+live graph data paths | boolean checks; headroom by design at run 0 |

## Run 0 baseline (frozen)

Repo commit at freeze: recorded in the commit that adds `freeze_manifest.json`.
Trained checkpoint: `ckpt.pt` (val loss 0.2326, 10.75M params, corpus seed 1337, 8000 docs).

| Dim | Score |
|-----|-------|
| S1 coverage | 0.5063 |
| S2 rules | 0.6939 |
| S3 narration | 0.9931 |
| S4 retrieval | 0.7737 |
| S5 brain | 1.0000 |
| S6 dataflow | 0.6923 |
| S7 features | 0.2222 |
| **composite** | **0.7086** |

S1/S2/S6/S7 carry deliberate headroom at run 0 — the reportable universe, the golden rule
suite, and the feature/dataflow contracts describe where the project is *going*, and the RSI
loop closes the gap. S3/S5 start near ceiling; the loop must protect them (no regression) while
lifting the rest.

## Running

```
python exam/run_exam.py --run N        # official score for RSI run N (needs Ollama up for S5)
python exam/run_exam.py --only s2,s6   # dev subset (composite omitted)
```

Results land in `exam/results/run-N.json` with full per-check detail.
