import importlib.util
from pathlib import Path
from verifieds.detector.engine import analyze_file

ROOT = Path(".")

fixture_dir = ROOT / "tests" / "fixtures" / "array-queue-front-removal"
all_ok = True
for f in fixture_dir.glob("*.cpp"):
    findings = analyze_file(f)
    rule_findings = [x for x in findings if x.rule_id == "array-queue-front-removal"]
    expected = "pos" if f.name.startswith("pos") else "neg"
    result = len(rule_findings)
    ok = (expected == "pos" and result == 1) or (expected == "neg" and result == 0)
    if not ok:
        all_ok = False
    print(f"{f.name}: {expected} -> {result} findings  [{'OK' if ok else 'FAIL'}]")

print(f"\nAll OK: {all_ok}")
