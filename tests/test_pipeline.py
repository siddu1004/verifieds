"""Tests for verifieds.pipeline."""

import sys
from pathlib import Path
from typing import Any
import pytest

from verifieds.pipeline.engine import (
    PipelineEngine,
    apply_patch,
    make_verify_diff,
    run_pipeline,
)
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import (
    CandidateDraft,
    Finding,
    VerifyReport,
    WorkloadResult,
)

ROOT = Path(__file__).resolve().parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


@pytest.fixture(scope="session")
def sim_cli_path() -> Path:
    cli_path = ROOT / "build" / exe_name("sim_cli")
    assert cli_path.exists()
    return cli_path


class FakeProposer(OllamaProposer):
    """Fake proposer for deterministic testing without external LLM."""

    def __init__(self, drafts: list[CandidateDraft]) -> None:
        super().__init__()
        self._drafts = drafts

    def propose(self, finding: Finding, code: str) -> list[CandidateDraft]:
        _ = (finding, code)
        return self._drafts


def test_pipeline_accepted_rewrite(sim_cli_path: Path):
    draft = CandidateDraft(
        strategy="Replace array ready queue with min heap",
        diff="--- ReadyQueue.hpp\n+++ ReadyQueue.hpp\n",
        expected_complexity_after="O(log n)",
        risks=["Heap allocation overhead for small n"],
    )
    fake_proposer = FakeProposer([draft])

    engine = PipelineEngine(proposer=fake_proposer, sizes=[20, 50], runs_per_size=3)
    target = ROOT / "sim" / "src" / "ReadyQueue.hpp"

    results = engine.run_on_file(
        source_path=target,
        orig_cmd=[str(sim_cli_path)],
        cand_cmd_builder=lambda _c: [str(sim_cli_path)],
    )

    assert len(results) >= 1
    finding, candidate, report = results[0]
    assert finding.rule_id in ("linear-min-extract", "array-queue-front-removal")
    assert candidate.strategy == draft.strategy
    assert report.equivalent is True
    assert report.speedup_at_max_n is not None
    assert report.speedup_at_max_n > 0.0


def test_pipeline_rejected_wrong_rewrite(tmp_path: Path):
    draft = CandidateDraft(
        strategy="Broken queue implementation",
        diff="invalid diff",
        expected_complexity_after="O(1)",
        risks=["Wrong results"],
    )
    fake_proposer = FakeProposer([draft])

    orig_script = tmp_path / "orig.py"
    cand_script = tmp_path / "cand.py"

    orig_script.write_text(
        'print(\'{"status": "ok", "gantt": []}\')\n', encoding="utf-8"
    )
    cand_script.write_text(
        'print(\'{"status": "wrong", "gantt": []}\')\n', encoding="utf-8"
    )

    engine = PipelineEngine(proposer=fake_proposer, sizes=[10], runs_per_size=2)
    target = ROOT / "sim" / "src" / "ReadyQueue.hpp"

    py = [sys.executable]
    results = engine.run_on_file(
        source_path=target,
        orig_cmd=py + [str(orig_script)],
        cand_cmd_builder=lambda _c: py + [str(cand_script)],
    )

    assert len(results) >= 1
    _, _, report = results[0]
    assert report.equivalent is False
    assert report.rejected_reason is not None
    assert report.speedup_at_max_n is None


def test_apply_patch_empty_and_invalid(tmp_path: Path):
    assert apply_patch(tmp_path, "") is True
    assert apply_patch(tmp_path, "invalid patch content\n") is False


def test_make_verify_diff_errors(tmp_path: Path):
    def bad_compile_orig(_s_dir: Path, _main: str, _out: Path) -> None:
        raise RuntimeError("orig build failed")

    verify_fn = make_verify_diff(
        compile_fn=bad_compile_orig,
        compare_fn=lambda *_a: None,
        workspace=tmp_path,
    )
    rep = verify_fn(tmp_path, "main.cpp", "", "cand1")
    assert rep.equivalent is False
    assert "Original build error" in (rep.rejected_reason or "")

    def bad_compile_cand(_s_dir: Path, _main: str, out: Path) -> None:
        if "cand_" in str(out):
            raise RuntimeError("cand build failed")

    verify_fn2 = make_verify_diff(
        compile_fn=bad_compile_cand,
        compare_fn=lambda *_a: None,
        workspace=tmp_path,
    )
    rep2 = verify_fn2(tmp_path, "main.cpp", "", "cand2")
    assert rep2.equivalent is False
    assert "Compile error" in (rep2.rejected_reason or "")

    # Compare error
    def bad_compare(*_a: Any) -> None:
        raise RuntimeError("compare crash")

    verify_fn3 = make_verify_diff(
        compile_fn=lambda *_a: None,
        compare_fn=bad_compare,
        workspace=tmp_path,
    )
    rep3 = verify_fn3(tmp_path, "main.cpp", "", "cand3")
    assert rep3.equivalent is False
    assert "Execution error" in (rep3.rejected_reason or "")

    # Rejected diff patch
    verify_fn4 = make_verify_diff(
        compile_fn=lambda *_a: None,
        compare_fn=lambda *_a: None,
        workspace=tmp_path,
    )
    rep4 = verify_fn4(tmp_path, "main.cpp", "invalid patch content\n", "cand4")
    assert rep4.equivalent is False
    assert "diff does not apply" in (rep4.rejected_reason or "")

    # workspace=None default creation
    verify_fn5 = make_verify_diff(
        compile_fn=bad_compile_orig,
        compare_fn=lambda *_a: None,
        workspace=None,
    )
    rep5 = verify_fn5(tmp_path, "main.cpp", "", "cand5")
    assert rep5.equivalent is False


def test_run_pipeline(tmp_path: Path):
    draft = CandidateDraft(
        strategy="Test strategy",
        diff="",
        expected_complexity_after="O(1)",
        risks=[],
    )
    fake_proposer = FakeProposer([draft])

    dummy_finding = Finding(
        id="f1",
        rule_id="r1",
        file="ReadyQueue.hpp",
        start_line=1,
        end_line=5,
        adt="priority_queue",
        impl="linear min-scan",
        complexity_before="O(n)",
        evidence="test evidence",
    )

    def dummy_detect(_p: Path) -> list[Finding]:
        return [dummy_finding]

    def dummy_compile(_s_dir: Path, _main: str, out: Path) -> None:
        out.write_text("binary", encoding="utf-8")

    def dummy_compare(
        _orig: Path, _cand: Path, cid: str, _sizes: list[int], _runs: int, _seed: int
    ) -> VerifyReport:
        wl = WorkloadResult(
            n=10, original_ms_median=10.0, candidate_ms_median=5.0, runs=5
        )
        return VerifyReport(
            candidate_id=cid,
            equivalent=True,
            workloads=[wl],
            speedup_at_max_n=2.0,
        )

    target_dir = ROOT / "sim" / "src"
    reports = run_pipeline(
        source_dir=target_dir,
        main_file="ReadyQueue.hpp",
        proposer=fake_proposer,
        workspace=tmp_path,
        detect=dummy_detect,
        compile_fn=dummy_compile,
        compare=dummy_compare,
        sizes=[10],
        runs=2,
    )
    assert len(reports) == 1
    assert reports[0].equivalent is True
