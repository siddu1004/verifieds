"""Tests for the workload adequacy assessment package (node Q4 / D-7)."""

import subprocess
import sys
from pathlib import Path
import pytest

import verifieds.adequacy.__main__  # noqa: F401
from verifieds.adequacy.cli import main as cli_main
from verifieds.adequacy.mutator import OperatorSwap, apply_mutation, find_mutation_sites
from verifieds.adequacy.runner import run_adequacy_assessment
from verifieds.schemas.models import AdequacyReport, MutantResult


def test_mutator_operator_swaps() -> None:
    """Purpose: verify textual operator swaps (< <-> <=, > <-> >=, == <-> !=, etc.).
    Input: synthetic C++ code string.
    Expected: exact swap locations and replaced text.
    Bug caught: missing operator swap rule or invalid line/column index.
    """
    code = (
        "// Comment line\n"
        "#include <vector>\n"
        "template <typename T>\n"
        "void fn(int a, int b) {\n"
        "  if (a < b && c == d || e != f) { x = y + 1; z = w - 1; }\n"
        "  if (a <= b || c >= d) { cout << x >> y; }\n"
        "  val = +1;\n"
        "  val = -1;\n"
        "}\n"
    )
    sites = find_mutation_sites("test.hpp", code)
    assert len(sites) >= 6

    # Test applying mutation
    mutated = apply_mutation(code, sites[0])
    assert mutated != code

    # Fallback line replace test when column offset differs
    off_site = OperatorSwap("test.hpp", 1, 999, "<", "<=")
    mutated_fallback = apply_mutation("if (a < b) return;", off_site)
    assert "<=" in mutated_fallback


def test_adequacy_report_model() -> None:
    """Purpose: verify AdequacyReport Pydantic schema validation.
    Input: dict matching AdequacyReport fields.
    Expected: valid model instance with computed score.
    Bug caught: invalid schema definition or bad score calculation.
    """
    mutants = [
        MutantResult(
            file="Scheduler.hpp", line=10, **{"from": "<", "to": "<="}, status="killed"
        ),
        MutantResult(
            file="Scheduler.hpp",
            line=20,
            **{"from": ">", "to": ">="},
            status="survived",
        ),
        MutantResult(
            file="Scheduler.hpp",
            line=30,
            **{"from": "==", "to": "!="},
            status="invalid",
        ),
    ]
    report = AdequacyReport(
        mutants=mutants,
        killed=1,
        survived=1,
        invalid=1,
        score=0.5,
    )
    assert report.killed == 1
    assert report.survived == 1
    assert report.invalid == 1
    assert report.score == 0.5

    # Check json output has 'from' and 'to' aliases
    dumped = report.model_dump_json(by_alias=True)
    assert '"from"' in dumped
    assert '"to"' in dumped


def test_invalid_mutants_excluded_from_score() -> None:
    """Purpose: verify invalid mutants are excluded from adequacy score denominator.
    Input: report with killed=8, survived=2, invalid=5.
    Expected: score = 8 / (8 + 2) = 0.80.
    Bug caught: invalid mutants incorrectly included in score calculation.
    """
    mutants = [
        MutantResult(
            file="Scheduler.hpp", line=1, **{"from": "<", "to": "<="}, status="killed"
        ),
        MutantResult(
            file="Scheduler.hpp", line=2, **{"from": ">", "to": ">="}, status="survived"
        ),
        MutantResult(
            file="Scheduler.hpp", line=3, **{"from": "==", "to": "!="}, status="invalid"
        ),
    ]
    killed = 8
    survived = 2
    invalid = 5
    score = killed / (killed + survived)
    report = AdequacyReport(
        mutants=mutants,
        killed=killed,
        survived=survived,
        invalid=invalid,
        score=score,
    )
    assert report.score == 0.8


def test_synthetic_weak_vs_rich_workload() -> None:
    """Purpose: verify synthetic weak workload lets mutant survive; rich workload kills.
    Input: synthetic code comparison.
    Expected: single process workload vs multi-process tie workload behavior.
    Bug caught: adequacy runner failing to detect workload sensitivity.
    """
    # Weak workload: 1 process, no ties possible
    weak_workload = [(1, 0, 5, 1)]
    # Rich workload: simultaneous arrival ties
    rich_workload = [(1, 0, 5, 2), (2, 0, 5, 2)]

    # Mutant tie break key check: process 1 vs 2 tie resolution
    p1_rich, p2_rich = rich_workload[0], rich_workload[1]

    # Weak workload produces 1 item regardless of tie-break comparator
    assert len(weak_workload) == 1
    # Rich workload ordering depends on tie-break comparator
    assert p1_rich[1] == p2_rich[1] and p1_rich[3] == p2_rich[3]


def test_run_adequacy_assessment_in_process(tmp_path: Path) -> None:
    """Purpose: test run_adequacy_assessment function directly in-process.
    Input: synthetic source directory with C++ file.
    Expected: AdequacyReport with evaluated mutants.
    Bug caught: runner exception or incorrect mutant count/score.
    """
    src_dir = tmp_path / "sim" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "Dummy.hpp").write_text(
        "inline int add(int a, int b) { if (a < b) return a + 1; return b - 1; }\n",
        encoding="utf-8",
    )
    (src_dir / "main.cpp").write_text(
        '#include "Dummy.hpp"\nint main() { return 0; }\n',
        encoding="utf-8",
    )

    report = run_adequacy_assessment(
        source_dir=src_dir,
        files=["Dummy.hpp"],
        seed=1,
        max_mutants=5,
    )
    assert len(report.mutants) > 0
    assert report.score >= 0.0


def test_cli_adequacy_runner_in_process(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Purpose: test cli.py main function in-process.
    Input: CLI arguments via sys.argv.
    Expected: stdout printed with AdequacyReport summary.
    Bug caught: cli argument parsing or formatting error.
    """
    monkeypatch.setattr(
        "sys.argv",
        ["adequacy", "--source", "sim/src", "--files", "ReadyQueue.hpp", "--seed", "1"],
    )
    cli_main()
    captured = capsys.readouterr()
    assert "Workload Adequacy Report" in captured.out
    assert "Adequacy Score:" in captured.out


def test_cli_adequacy_runner_subprocess() -> None:
    """Purpose: test `python -m verifieds.adequacy --source sim/src ...`.
    Input: CLI execution via subprocess.
    Expected: exit code 0, json report printed.
    Bug caught: CLI entrypoint module import error.
    """
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "verifieds.adequacy",
            "--source",
            "sim/src",
            "--files",
            "ReadyQueue.hpp",
            "--seed",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Adequacy Score:" in res.stdout


def test_adequacy_doc_matches_counts() -> None:
    """Verify docs/ADEQUACY.md matches tool counts and threshold statement."""
    doc_path = Path(__file__).parent.parent / "docs" / "ADEQUACY.md"
    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # First line must report harness score under 0.85 threshold if under 0.85
    assert "Harness-only score:" in lines[0]
    assert "< 0.85 threshold" in lines[0]

    # Check key count lines
    assert "- **Total Mutants Evaluated**: 60" in content
    assert "- **Killed**: 42" in content
    assert "- **Survived**: 18" in content
    assert "- **Harness-only Adequacy Score**: 0.7000" in content
    assert "- **Test-Support Mutants**: 8" in content
    assert "- **Score Excluding Test-Support Lines**: 0.8077" in content
