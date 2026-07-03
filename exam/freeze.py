# freeze.py — write freeze_manifest.json (SHA256 of every frozen exam file). Run ONCE at run 0.
# After this, run_exam.py's verify_frozen() fails loudly if any exam file is edited — so an RSI
# contender can't quietly weaken the questions to inflate its score.
import hashlib, json, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from run_exam import FROZEN_FILES  # noqa: E402

manifest = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in FROZEN_FILES}
(HERE / "freeze_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("froze", len(manifest), "files:")
for k, v in manifest.items():
    print(f"  {v[:12]}  {k}")
