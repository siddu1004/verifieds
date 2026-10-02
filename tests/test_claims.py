"""Test suite validating claims audit table in docs/CLAIMS.md (T6)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_claims_audit_table_valid() -> None:
    """Verify docs/CLAIMS.md parses correctly and all referenced tests exist."""
    claims_path = ROOT / "docs" / "CLAIMS.md"
    assert claims_path.exists(), "docs/CLAIMS.md must exist"

    readme_path = ROOT / "README.md"
    assert readme_path.exists()

    content = claims_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    claims_rows: list[tuple[str, str, str]] = []
    for line in lines:
        if not line.startswith("|") or "Source" in line or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            source, claim_text, test_fn = parts[1], parts[2], parts[3]
            claims_rows.append((source, claim_text, test_fn))

    assert len(claims_rows) >= 5, (
        f"Expected at least 5 claims rows, found {len(claims_rows)}"
    )

    # Check every claim from README has a row in CLAIMS.md
    readme_claims = [
        "detects data-structure and algorithm bottlenecks",
        "proposes optimizations using a local LLM",
        "accepts changes only if proven equivalent",
        "Resource limits on Windows",
        "process timeout limits",
    ]
    claims_text_concat = " ".join(r[1] for r in claims_rows)
    for rc in readme_claims:
        assert rc in claims_text_concat or any(
            rc.lower() in r[1].lower() for r in claims_rows
        ), f"README claim {rc!r} has no matching row in docs/CLAIMS.md"

    # Verify every referenced test function exists
    for _source, claim_text, test_ref in claims_rows:
        test_ref_clean = test_ref.strip("`")
        assert "::" in test_ref_clean, f"Invalid test format: {test_ref_clean}"
        file_part, fn_part = test_ref_clean.split("::", 1)

        test_file = ROOT / file_part
        assert test_file.exists(), (
            f"Referenced test file {file_part} missing for claim {claim_text!r}"
        )

        # Inspect file content to verify function/test definition exists
        file_text = test_file.read_text(encoding="utf-8")
        assert re.search(rf"\bdef {re.escape(fn_part)}\b", file_text), (
            f"Referenced test {fn_part} not found in {file_part} for {claim_text!r}"
        )
