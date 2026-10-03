"""Test suite validating claims audit table in docs/CLAIMS.md (T6 / R-07)."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_keywords(claim_text: str) -> list[str]:
    """Extract relevant search keywords from claim text."""
    stop_words = {
        "and",
        "or",
        "in",
        "on",
        "per",
        "via",
        "the",
        "a",
        "an",
        "is",
        "by",
        "to",
        "of",
        "for",
        "with",
        "does",
        "not",
        "such",
        "as",
        "only",
        "if",
        "using",
        "proven",
        "measurably",
        "core",
        "results",
        "point",
        "text",
        "source",
        "claim",
        "table",
        "audit",
        "based",
    }
    words = re.findall(r"\b[A-Za-z0-9]+\b", claim_text)
    keywords = [w.lower() for w in words if w.lower() not in stop_words and len(w) >= 3]
    return keywords


def get_function_source(file_path: Path, fn_name: str) -> str:
    """Extract full source text of target function using AST parsing."""
    code = file_path.read_text(encoding="utf-8")
    tree = ast.parse(code, filename=str(file_path))
    lines = code.splitlines()

    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == fn_name
        ):
            start = node.lineno - 1
            end = node.end_lineno if node.end_lineno is not None else start + 10
            return "\n".join(lines[start:end])

    raise ValueError(f"Function {fn_name} not found in {file_path}")


def test_claims_audit_table_valid() -> None:
    """Verify docs/CLAIMS.md parses correctly and claim keywords exist."""
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
        "Proposes candidate optimizations using local Ollama LLM",
        "accepts changes only if verified equivalent",
        "Resource limits on Windows",
        "process timeout limits",
        "diagnostics tool",
        "MCP server stdio interface",
        "generic C++ project",
        "Workspace root environment override",
    ]
    claims_text_concat = " ".join(r[1] for r in claims_rows)
    for rc in readme_claims:
        assert rc in claims_text_concat or any(
            rc.lower() in r[1].lower() for r in claims_rows
        ), f"README claim {rc!r} has no matching row in docs/CLAIMS.md"

    # Verify every referenced test function exists AND contains a claim keyword
    for _source, claim_text, test_ref in claims_rows:
        test_ref_clean = test_ref.strip("`")
        assert "::" in test_ref_clean, f"Invalid test format: {test_ref_clean}"
        file_part, fn_part = test_ref_clean.split("::", 1)

        test_file = ROOT / file_part
        assert test_file.exists(), (
            f"Referenced test file {file_part} missing for claim {claim_text!r}"
        )

        fn_source = get_function_source(test_file, fn_part).lower()
        keywords = extract_keywords(claim_text)
        assert len(keywords) > 0, f"No keywords extracted from claim {claim_text!r}"

        # Assert at least one claim keyword is present in the test source
        keyword_found = any(kw in fn_source for kw in keywords)
        err_msg = (
            f"None of keywords {keywords} for claim {claim_text!r} "
            f"found in test source of {fn_part} ({file_part})"
        )
        assert keyword_found, err_msg
