"""Tests for verifieds.pipeline."""

import sys
from pathlib import Path
import pytest

from verifieds.pipeline.engine import PipelineEngine
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import CandidateDraft, Finding

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
