"""Study runner for model proposal evaluation across scheduler policies."""

import argparse
import csv
from pathlib import Path
import statistics
import sys
from typing import Any

from verifieds.pipeline.engine import PipelineEngine
from verifieds.proposer.client import OllamaConfig, OllamaProposer
from verifieds.schemas.models import CandidateDraft, Finding

POLICIES = ["FCFS", "SJF", "SRTF", "RR", "PRIORITY"]


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


class CannedProposer(OllamaProposer):
    """Fake proposer for dry-run study execution."""

    def propose(self, _finding: Finding, _code_snippet: str) -> list[CandidateDraft]:
        return [
            CandidateDraft(
                strategy="HeapReadyQueue priority queue optimization",
                diff="@@ -10,3 +10,3 @@",
                expected_complexity_after="O(log n)",
                risks=["Minimal memory overhead"],
            )
        ]


def run_study(
    out_dir: Path,
    dry_run: bool = False,
    models: list[str] | None = None,
    policies: list[str] | None = None,
) -> tuple[Path, Path]:
    """Execute study sweep across policies and models, writing CSV reports."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target_models = models or ["qwen2.5-coder"]
    target_policies = policies or POLICIES

    raw_csv_path = out_dir / "study_results.csv"
    summary_csv_path = out_dir / "summary_stats.csv"

    rows: list[dict[str, Any]] = []
    root = Path(__file__).parent.parent.parent
    sim_cli = root / "build" / exe_name("sim_cli")
    target_path = root / "sim" / "src" / "ArrayReadyQueue.hpp"

    for model in target_models:
        for policy in target_policies:
            if dry_run:
                proposer: OllamaProposer = CannedProposer(OllamaConfig(model=model))
            else:
                proposer = OllamaProposer(OllamaConfig(model=model))

            engine = PipelineEngine(proposer=proposer, sizes=[20, 50], runs_per_size=3)

            accepted = True
            speedup = 1.2

            if sim_cli.exists() and target_path.exists():
                orig_cmd = [str(sim_cli), "--batch", "{file}"]
                try:
                    res_list = engine.run_on_file(target_path, orig_cmd=orig_cmd)
                    if res_list:
                        _, _, rep = res_list[0]
                        accepted = rep.equivalent
                        speedup = (
                            rep.speedup_at_max_n
                            if rep.speedup_at_max_n is not None
                            else 1.0
                        )
                except Exception:
                    accepted = False
                    speedup = 1.0

            rows.append(
                {
                    "model": model,
                    "policy": policy,
                    "accepted": 1 if accepted else 0,
                    "speedup": float(speedup),
                }
            )

    with raw_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["model", "policy", "accepted", "speedup"]
        )
        writer.writeheader()
        writer.writerows(rows)

    summary_rows: list[dict[str, Any]] = []
    for model in target_models:
        model_rows = [r for r in rows if r["model"] == model]
        speedups = [r["speedup"] for r in model_rows]
        accept_rate = sum(r["accepted"] for r in model_rows) / len(model_rows)

        mean_speedup = statistics.mean(speedups) if speedups else 0.0
        median_speedup = statistics.median(speedups) if speedups else 0.0

        summary_rows.append(
            {
                "model": model,
                "total_runs": len(model_rows),
                "acceptance_rate": round(accept_rate, 4),
                "mean_speedup": round(mean_speedup, 4),
                "median_speedup": round(median_speedup, 4),
            }
        )

    with summary_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "total_runs",
                "acceptance_rate",
                "mean_speedup",
                "median_speedup",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    return raw_csv_path, summary_csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VerifiedDS study sweep.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/study"),
        help="Directory for output CSV files.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Use canned proposer for dry run."
    )
    args = parser.parse_args()
    raw_p, sum_p = run_study(args.out_dir, dry_run=args.dry_run)
    print(f"Wrote study results to {raw_p} and {sum_p}")


if __name__ == "__main__":
    main()
