"""CLI entry point for workload adequacy assessment (node Q4 / D-7)."""

import argparse
from pathlib import Path

from verifieds.adequacy.runner import run_adequacy_assessment


def main() -> None:
    """CLI entry point for `python -m verifieds.adequacy`."""
    parser = argparse.ArgumentParser(
        description="Run workload adequacy mutation assessment."
    )
    parser.add_argument(
        "--source",
        default="sim/src",
        help="Source directory containing C++ files (default: sim/src)",
    )
    parser.add_argument(
        "--files",
        default="Scheduler.hpp,ReadyQueue.hpp",
        help="Comma-separated list of C++ header files to mutate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Random seed for workload generation (default: 1)",
    )

    args = parser.parse_args()
    files_list = [f.strip() for f in args.files.split(",") if f.strip()]

    report = run_adequacy_assessment(
        source_dir=Path(args.source),
        files=files_list,
        seed=args.seed,
    )

    print("\n--- Workload Adequacy Report ---")
    print(f"Total Mutants Evaluated: {len(report.mutants)}")
    print(f"Killed:   {report.killed}")
    print(f"Survived: {report.survived}")
    print(f"Invalid:  {report.invalid}")
    print(f"Adequacy Score: {report.score:.4f}")
    print(
        "Note: Survivors may be equivalent mutants; the score is a lower-bound\n"
        "indicator of how well the workloads can detect behavioural change, "
        "not a proof.\n"
    )

    # Print raw JSON report
    report_json = report.model_dump_json(indent=2, by_alias=True)
    print(report_json)


if __name__ == "__main__":
    main()
