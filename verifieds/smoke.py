import argparse
import sys
from pathlib import Path

from verifieds.detector.engine import analyze_file
from verifieds.proposer.client import (
    OllamaConfig,
    OllamaParseError,
    OllamaProposer,
    OllamaUnavailableError,
)
from verifieds.wiring import build_verify_diff


def main() -> None:
    parser = argparse.ArgumentParser(description="Live model smoke test for VerifiedDS")
    parser.add_argument("--file", required=True, help="Path to C++ source file")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)

    print(f"Scanning file: {file_path}")
    findings = analyze_file(file_path)
    if not findings:
        print("No DS/Algo inefficiency findings detected in file.")
        sys.exit(0)

    first_finding = findings[0]
    print(
        f"Finding detected: {first_finding.id} ({first_finding.adt}) "
        f"at line {first_finding.start_line}"
    )

    config = OllamaConfig()
    print(f"Calling Ollama at {config.base_url} with model {config.model}...")
    proposer = OllamaProposer(config=config)

    code = file_path.read_text(encoding="utf-8")
    try:
        candidates = proposer.propose(first_finding, code)
    except (OllamaUnavailableError, OllamaParseError) as err:
        print(f"Skipped verification: Ollama call failed: {err}")
        sys.exit(0)

    if not candidates:
        print("Skipped verification: No candidate proposals returned by Ollama.")
        sys.exit(0)

    cand = candidates[0]

    print("\n--- Proposed Strategy ---")
    print(cand.strategy)
    print("\n--- Proposed Diff ---")
    print(cand.diff)

    proj_dir = file_path.parent
    main_file = file_path.name

    print("\nVerifying candidate diff...")
    verify_diff_fn = build_verify_diff(
        workspace=proj_dir,
        sizes=(200, 2000, 8000),
        runs=3,
    )

    try:
        report = verify_diff_fn(
            source_dir=proj_dir,
            main_file=main_file,
            diff=cand.diff,
            candidate_id="smoke_cand_1",
        )
    except Exception as err:
        print(f"Skipped verification: Compilation or build failed: {err}")
        sys.exit(0)

    if report.equivalent:
        print(f"Verification PASSED! Speedup: {report.speedup_at_max_n}")
    else:
        print(f"Verification REJECTED: {report.rejected_reason}")


if __name__ == "__main__":
    main()
