import argparse
import sys
from pathlib import Path

from verifieds.detector.engine import analyze_file
from verifieds.mcp.server import verify_candidate
from verifieds.proposer.client import (
    OllamaConfig,
    OllamaParseError,
    OllamaProposer,
    OllamaUnavailableError,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Live model smoke test for VerifiedDS")
    parser.add_argument("--file", required=True, help="Path to C++ source file")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verify_candidate on the first applicable candidate",
    )
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

    print(f"Obtained {len(candidates)} candidate proposal(s).")
    for idx, cand in enumerate(candidates, 1):
        print(f"\n--- Candidate {idx} Strategy ---")
        print(cand.strategy)
        print(f"--- Candidate {idx} Diff ---")
        print(cand.diff)

    if not args.verify:
        print(
            "\nSmoke test proposal completed (pass --verify to run verify_candidate)."
        )
        sys.exit(0)

    # With --verify: find first applicable candidate and run verify_candidate
    target_cand = None
    target_id = "smoke_cand_1"
    for idx, cand in enumerate(candidates, 1):
        if cand.diff and cand.diff.strip():
            target_cand = cand
            target_id = f"smoke_cand_{idx}"
            break

    if target_cand is None:
        target_cand = candidates[0]

    # Resolve project directory and main file relative to repo root if inside sim/
    repo_root = file_path.parent.parent
    project_dir = (
        str(repo_root / "sim")
        if (repo_root / "sim").exists()
        else str(file_path.parent)
    )
    main_file = "src/main.cpp" if (repo_root / "sim").exists() else file_path.name

    print(f"\nRunning verify_candidate on candidate '{target_id}'...")
    res = verify_candidate(
        project_dir=project_dir,
        main_file=main_file,
        diff=target_cand.diff,
        candidate_id=target_id,
    )

    print("\n=== VerifyReport ===")
    print(f"candidate_id: {res.get('candidate_id')}")
    print(f"equivalent: {res.get('equivalent')}")
    print(f"rejected_reason: {res.get('rejected_reason')}")
    print(f"speedup_at_max_n: {res.get('speedup_at_max_n')}")
    print(f"workloads: {res.get('workloads')}")


if __name__ == "__main__":
    main()
