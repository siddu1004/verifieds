"""Pipeline engine orchestrating detector, proposer, harness, and reporter."""

from pathlib import Path
from typing import Any

from verifieds.detector.engine import analyze_file
from verifieds.harness.runner import BenchmarkRunner
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import Candidate, Finding, VerifyReport, WorkloadResult


class PipelineEngine:
    """Orchestrates detector, proposer, harness, and reporting."""

    def __init__(
        self,
        proposer: OllamaProposer | None = None,
        sizes: list[int] | None = None,
        runs_per_size: int = 7,
    ) -> None:
        self.proposer = proposer or OllamaProposer()
        self.sizes = sizes or [100, 1000, 10000]
        self.runs_per_size = runs_per_size

    def run_on_file(
        self,
        source_path: Path,
        orig_cmd: list[str],
        cand_cmd_builder: Any | None = None,
    ) -> list[tuple[Finding, Candidate, VerifyReport]]:
        """Run complete pipeline on a target source file."""
        findings = analyze_file(source_path)
        results: list[tuple[Finding, Candidate, VerifyReport]] = []

        code = source_path.read_text(encoding="utf-8")

        for finding in findings:
            drafts = self.proposer.propose(finding, code)

            for idx, draft in enumerate(drafts):
                cand_id = f"cand_{finding.id}_{idx + 1}"
                candidate = Candidate(
                    id=cand_id,
                    finding_id=finding.id,
                    strategy=draft.strategy,
                    diff=draft.diff,
                    expected_complexity_after=draft.expected_complexity_after,
                    risks=draft.risks,
                )

                cand_cmd = cand_cmd_builder(candidate) if cand_cmd_builder else orig_cmd

                runner = BenchmarkRunner(
                    orig_cmd=orig_cmd,
                    cand_cmd=cand_cmd,
                    runs_per_size=self.runs_per_size,
                )
                bench_res = runner.run_benchmark(sizes=self.sizes)

                if not bench_res["equivalent"]:
                    report = VerifyReport(
                        candidate_id=cand_id,
                        equivalent=False,
                        rejected_reason=bench_res.get("reason", "Output mismatch"),
                        workloads=[],
                        speedup_at_max_n=None,
                        crossover_n=None,
                    )
                else:
                    workloads = [
                        WorkloadResult(
                            n=n,
                            original_ms_median=bench_res["medians_orig"][n] * 1000.0,
                            candidate_ms_median=bench_res["medians_cand"][n] * 1000.0,
                            runs=self.runs_per_size,
                        )
                        for n in self.sizes
                    ]
                    report = VerifyReport(
                        candidate_id=cand_id,
                        equivalent=True,
                        rejected_reason=None,
                        workloads=workloads,
                        speedup_at_max_n=bench_res["speedup_at_max_n"],
                        crossover_n=bench_res["crossover_n"],
                    )

                results.append((finding, candidate, report))

        return results


def run_pipeline(
    source_path: Path,
    orig_cmd: list[str],
    proposer: OllamaProposer | None = None,
) -> list[tuple[Finding, Candidate, VerifyReport]]:
    """Convenience function for pipeline execution."""
    engine = PipelineEngine(proposer=proposer)
    return engine.run_on_file(source_path, orig_cmd)
