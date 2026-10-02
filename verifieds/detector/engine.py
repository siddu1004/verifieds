"""Detector engine that runs loaded rules against source files to yield Findings."""

import hashlib
from pathlib import Path
from verifieds.detector.loader import load_rules
from verifieds.detector.scanner import SourceView
from verifieds.schemas.models import Finding


def analyze_file(filepath: str | Path) -> list[Finding]:
    """Analyze a single C++ source or header file for performance findings."""
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    code = path.read_text(encoding="utf-8", errors="replace")
    source_view = SourceView(code)
    rules = load_rules()

    file_repr = path.name

    findings: list[Finding] = []

    for rule in rules:
        matches = rule["matcher"](source_view)
        for start_line, end_line, evidence in matches:
            raw_key = f"{rule['rule_id']}|{file_repr}|{start_line}|{end_line}"
            finding_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

            finding = Finding(
                id=finding_id,
                rule_id=rule["rule_id"],
                file=file_repr,
                start_line=start_line,
                end_line=end_line,
                adt=rule["adt"],
                impl=rule["impl"],
                complexity_before=rule["complexity_before"],
                evidence=evidence,
            )
            findings.append(finding)

    # Sort findings by file then start_line
    findings.sort(key=lambda f: (f.file, f.start_line))
    return findings
