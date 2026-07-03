# _ui_robustness.py — exam helper: the GUI panel path must survive hostile remote snapshots.
# The /ingest boundary admits any JSON dict as `snap`; everything the panel tick touches
# (schema.summarize, rules.diagnose via context.snapshot_and_findings, the markdown assembly)
# must degrade, not raise. Fresh interpreter. Prints "ui robust ok" iff nothing crashes.
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import schema, rules  # noqa: E402

HOSTILE = [
    {"cpu": {"load": [1, 2]}},                                  # list where number belongs
    {"cpu": {"load": "high"}},                                  # string where number belongs
    {"cpu": "pwn"},                                             # string where dict belongs
    {"sensors": {"cpu_temp": {"deep": {"deeper": 1}}}},         # dict where number belongs
    {"gpu": {"temp": float("nan"), "power": float("inf")}},     # non-finite numbers
    {"mem": {"pct": None}, "disk": None, "whea": []},           # nulls and wrong containers
    {"_errors": "oops-string", "_note": "# heading\n**bold** <script>alert(1)</script>"},
    {"_tags": {"k" * 500: "v" * 5000}, "_label": "x" * 10000},  # oversized metadata
    {"disk": {"C": 50, "__proto__": 99, "": 42}},               # weird keys
]


def main():
    for i, snap in enumerate(HOSTILE):
        try:
            schema.summarize(snap)
        except Exception as e:
            print(f"summarize crashed on hostile snap #{i}: {type(e).__name__}: {e}")
            return
        try:
            rules.diagnose(snap)
        except Exception as e:
            print(f"diagnose crashed on hostile snap #{i}: {type(e).__name__}: {e}")
            return
    print("ui robust ok")


if __name__ == "__main__":
    main()
