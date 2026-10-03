"""Demo runner test suite regenerating results/demo.md deterministically (T6 / R-08)."""

import difflib
import json
from pathlib import Path

from tests.reference_scheduler import schedule
from tests.test_reference_scheduler import SET_A
from verifieds.detector.engine import analyze_file
from verifieds.schemas.models import AdequacyReport
from verifieds.wiring import build_verify_diff

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
DEMO_MD = RESULTS_DIR / "demo.md"
ADEQUACY_JSON = RESULTS_DIR / "adequacy.json"


def get_diff_pa() -> str:
    config_file = ROOT / "sim" / "src" / "Config.hpp"
    orig_config = config_file.read_text(encoding="utf-8")
    cand_config = orig_config.replace(
        'constexpr std::string_view kDefaultBackend = "array";',
        'constexpr std::string_view kDefaultBackend = "heap";',
    )
    diff_lines = list(
        difflib.unified_diff(
            orig_config.splitlines(keepends=True),
            cand_config.splitlines(keepends=True),
            fromfile="a/src/Config.hpp",
            tofile="b/src/Config.hpp",
        )
    )
    return "".join(diff_lines)


def get_diff_pb() -> str:
    config_file = ROOT / "sim" / "src" / "Config.hpp"
    orig_config = config_file.read_text(encoding="utf-8")
    cand_config = orig_config.replace(
        'constexpr std::string_view kDefaultBackend = "array";',
        'constexpr std::string_view kDefaultBackend = "heap";',
    )
    diff_config = "".join(
        difflib.unified_diff(
            orig_config.splitlines(keepends=True),
            cand_config.splitlines(keepends=True),
            fromfile="a/src/Config.hpp",
            tofile="b/src/Config.hpp",
        )
    )

    rq_file = ROOT / "sim" / "src" / "ReadyQueue.hpp"
    orig_rq = rq_file.read_text(encoding="utf-8")
    cand_rq = orig_rq.replace(
        "return pid < other.pid;",
        "return false;",
    )
    diff_rq = "".join(
        difflib.unified_diff(
            orig_rq.splitlines(keepends=True),
            cand_rq.splitlines(keepends=True),
            fromfile="a/src/ReadyQueue.hpp",
            tofile="b/src/ReadyQueue.hpp",
        )
    )
    return diff_config + diff_rq


def generate_demo_content(workspace: Path | None = None) -> str:
    """Generate deterministic markdown report using real components.

    Contains NO dates, NO timestamps, and NO hardware timings to ensure
    byte-level reproducibility across consecutive runs.
    """

    lines: list[str] = [
        "# VerifiedDS End-to-End Execution Demo",
        "",
        "## 1. Baseline Simulation (Set A Workload)",
        "",
    ]

    gantt, _ = schedule(SET_A, "FCFS")
    gantt_str = " ".join(f"P{pid}[{start}-{end}]" for pid, start, end in gantt)
    lines.append(f"Gantt Schedule: `{gantt_str}`")
    lines.append("")

    lines.append("## 2. Static Bottleneck Detection (sim/src/ReadyQueue.hpp)")
    lines.append("")

    rq_path = ROOT / "sim" / "src" / "ReadyQueue.hpp"
    findings = analyze_file(rq_path) if rq_path.exists() else []

    lines.append(f"Findings Detected: {len(findings)}")
    for f in findings:
        lines.append(f"- [{f.rule_id}] Lines {f.start_line}-{f.end_line}: {f.evidence}")
    lines.append("")

    lines.append("## 3. Pipeline Candidate Verification")
    lines.append("")

    verify_diff = build_verify_diff(workspace=workspace, sizes=[20, 50], runs=2)
    rep1 = verify_diff(
        source_dir=ROOT / "sim",
        main_file="src/main.cpp",
        diff=get_diff_pa(),
        candidate_id="cand_heap_rewrite",
    )

    rep2 = verify_diff(
        source_dir=ROOT / "sim",
        main_file="src/main.cpp",
        diff=get_diff_pb(),
        candidate_id="cand_tiebreak_mutant",
    )

    lines.append(
        f"Candidate 1 (Array -> Heap Config Rewrite): Equivalent={rep1.equivalent}"
    )
    lines.append(
        f"Candidate 2 (Tie-break Mutant): "
        f"Equivalent={rep2.equivalent}, Reason={rep2.rejected_reason}"
    )
    lines.append("")

    lines.append("## 4. Workload Adequacy Assessment Summary")
    lines.append("")

    raw_json = ADEQUACY_JSON.read_text(encoding="utf-8")
    adeq_rep = AdequacyReport.model_validate(json.loads(raw_json))

    total_eval = len(adeq_rep.mutants)
    lines.append(f"- Total Mutants Evaluated: {total_eval}")
    lines.append(f"- Killed: {adeq_rep.killed}")
    lines.append(f"- Survived: {adeq_rep.survived}")
    lines.append(f"- Harness-only Adequacy Score: {adeq_rep.score:.4f}")
    lines.append(f"- Test-Support Mutants: {adeq_rep.test_support_count}")
    score_ex_val = adeq_rep.score_excluding_test_support
    lines.append(f"- Score Excluding Test-Support Lines: {score_ex_val:.4f}")

    lines.append("")

    return "\n".join(lines)


def test_demo_reproducible(tmp_path: Path) -> None:
    """Verify test_demo.py generates results/demo.md deterministically."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"

    content1 = generate_demo_content(workspace=ws1)
    DEMO_MD.write_text(content1, encoding="utf-8")

    content2 = generate_demo_content(workspace=ws2)
    assert content1 == content2, "results/demo.md generation must be byte-identical"
    assert DEMO_MD.exists()
