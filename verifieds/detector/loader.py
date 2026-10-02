"""Rule loader for verifieds detector rules."""

import importlib.util
import json
from pathlib import Path
from typing import Any, cast
from collections.abc import Callable
from verifieds.detector.scanner import SourceView

RuleMatchFunc = Callable[[SourceView], list[tuple[int, int, str]]]

ROOT = Path(__file__).resolve().parent.parent.parent
RULES_DIR = ROOT / "verifieds" / "rules"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def load_rules() -> list[dict[str, Any]]:
    """Load all rules from verifieds/rules/ and validate fixtures."""
    if not RULES_DIR.exists():
        raise FileNotFoundError(f"Rules directory not found: {RULES_DIR}")

    json_files = sorted(RULES_DIR.glob("*.json"))
    rules: list[dict[str, Any]] = []

    for jf in json_files:
        rule_id = jf.stem
        py_file = RULES_DIR / f"{rule_id}.py"
        if not py_file.exists():
            raise FileNotFoundError(f"Missing rule matcher script: {py_file}")

        # Check fixture directory
        fix_dir = FIXTURES_DIR / rule_id
        if not fix_dir.exists():
            raise FileNotFoundError(f"Missing fixture directory: {fix_dir}")

        pos_files = list(fix_dir.glob("pos_*.cpp"))
        neg_files = list(fix_dir.glob("neg_*.cpp"))
        if not pos_files or not neg_files:
            raise FileNotFoundError(
                f"Rule {rule_id} must have pos_*.cpp and neg_*.cpp "
                f"fixtures in {fix_dir}"
            )

        with jf.open("r", encoding="utf-8") as f:
            meta = json.load(f)

        # Import python matcher module
        spec = importlib.util.spec_from_file_location(f"rule_{rule_id}", py_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {py_file}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        raw_matcher = getattr(mod, "match", None)
        if raw_matcher is None:
            raise AttributeError(
                f"Rule script {py_file} must define a match(source_view) function"
            )
        matcher: RuleMatchFunc = cast(RuleMatchFunc, raw_matcher)

        meta["matcher"] = matcher
        rules.append(meta)

    return rules
