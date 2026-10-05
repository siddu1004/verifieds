"""Pipeline engine orchestrating detector, proposer, harness, and reporter."""

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

from verifieds.contracts import VerifyDiffFn
from verifieds.schemas.models import Candidate, Finding, VerifyReport


class PipelineEngine:
    """Orchestrates detector, proposer, harness, and reporting."""

    def __init__(
        self,
        proposer: Any | None = None,
        sizes: list[int] | None = None,
        runs_per_size: int = 7,
    ) -> None:
        from verifieds.proposer.client import OllamaProposer

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
        from verifieds.detector.engine import analyze_file
        from verifieds.harness.runner import BenchmarkRunner

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
                    candidate_id=cand_id,
                    runs_per_size=self.runs_per_size,
                )
                report = runner.run_benchmark(sizes=self.sizes)
                results.append((finding, candidate, report))

        return results


def is_diff_safe(target_dir: Path, diff: str) -> bool:
    """Check if all files modified by the diff are strictly within target_dir."""
    target_dir = target_dir.resolve()
    for line in diff.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            parts = line.split(maxsplit=1)
            if len(parts) > 1:
                raw_path = parts[1].strip()
                if raw_path.startswith("a/") or raw_path.startswith("b/"):
                    raw_path = raw_path[2:]
                if raw_path == "/dev/null" or not raw_path:
                    continue
                path_obj = Path(raw_path)
                if path_obj.is_absolute():
                    try:
                        resolved = path_obj.resolve()
                        resolved.relative_to(target_dir)
                    except ValueError:
                        return False
                else:
                    try:
                        resolved = (target_dir / path_obj).resolve()
                        resolved.relative_to(target_dir)
                    except ValueError:
                        return False
    return True


def apply_patch(target_dir: Path, diff: str) -> bool:
    """Apply a unified diff to files inside target_dir using git apply."""
    if not diff.strip():
        return True
    if not is_diff_safe(target_dir, diff):
        return False
    try:
        proc = subprocess.run(
            [
                "git",
                "apply",
                "--reject",
                "--whitespace=fix",
                "--ignore-space-change",
                "--ignore-whitespace",
            ],
            input=diff,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return True
        proc_p0 = subprocess.run(
            [
                "git",
                "apply",
                "--reject",
                "-p0",
                "--whitespace=fix",
                "--ignore-space-change",
                "--ignore-whitespace",
            ],
            input=diff,
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc_p0.returncode == 0
    except Exception:
        return False


def make_verify_diff(
    compile_fn: Any,
    compare_fn: Any,
    workspace: Path | None = None,
    sizes: tuple[int, ...] | list[int] = (100, 1000, 10000),
    runs: int = 7,
    seed: int = 1234,
) -> VerifyDiffFn:
    """Create a VerifyDiffFn bound to compile_fn and compare_fn."""

    def verify_diff(
        source_dir: Path,
        main_file: str,
        diff: str,
        candidate_id: str,
        workload_cmd: str | None = None,
    ) -> VerifyReport:
        nonlocal workspace
        if workspace is None:
            workspace_dir = Path(tempfile.mkdtemp(prefix="pipeline_ws_"))
        else:
            workspace_dir = workspace
            workspace_dir.mkdir(parents=True, exist_ok=True)

        cand_src = workspace_dir / f"src_{candidate_id}"
        shutil.rmtree(cand_src, ignore_errors=True)
        shutil.copytree(
            source_dir,
            cand_src,
            ignore=shutil.ignore_patterns(
                "src_*", "orig_*", "cand_*", "tmp*", ".git", "build"
            ),
        )

        # Apply patch to candidate source
        if not apply_patch(cand_src, diff):
            return VerifyReport(
                candidate_id=candidate_id,
                equivalent=False,
                rejected_reason="diff does not apply",
                workloads=[],
            )

        orig_exe = (
            workspace_dir / f"orig_{candidate_id}.exe"
            if sys.platform == "win32"
            else workspace_dir / f"orig_{candidate_id}"
        )
        cand_exe = (
            workspace_dir / f"cand_{candidate_id}.exe"
            if sys.platform == "win32"
            else workspace_dir / f"cand_{candidate_id}"
        )

        # Compile original binary
        try:
            compile_fn(source_dir, main_file, orig_exe)
        except Exception as err:
            return VerifyReport(
                candidate_id=candidate_id,
                equivalent=False,
                rejected_reason=f"Original build error: {err}",
                workloads=[],
            )

        # Compile candidate binary
        try:
            compile_fn(cand_src, main_file, cand_exe)
        except Exception as err:
            return VerifyReport(
                candidate_id=candidate_id,
                equivalent=False,
                rejected_reason=f"Compile error: {err}",
                workloads=[],
            )

        # Compare binaries
        try:
            res = compare_fn(
                orig_exe,
                cand_exe,
                candidate_id,
                list(sizes),
                runs,
                seed,
                workload_cmd=workload_cmd,
            )
            return cast(VerifyReport, res)
        except Exception as err:
            return VerifyReport(
                candidate_id=candidate_id,
                equivalent=False,
                rejected_reason=f"Execution error: {err}",
                workloads=[],
            )

    return verify_diff


def run_pipeline(
    source_dir: Path,
    main_file: str,
    proposer: Any,
    workspace: Path | None = None,
    *,
    detect: Any = None,
    compile_fn: Any = None,
    compare: Any = None,
    sizes: tuple[int, ...] | list[int] = (100, 1000, 10000),
    runs: int = 7,
    seed: int = 1234,
) -> list[VerifyReport]:
    """Run full pipeline on target file using injected dependency functions."""
    target_path = source_dir / main_file
    if detect is None:
        from verifieds.detector import detect_file

        detect = detect_file

    if compile_fn is None or compare is None:
        from verifieds.harness import compare as real_compare
        from verifieds.harness import compile_program as real_compile

        compile_fn = compile_fn or real_compile
        compare = compare or real_compare

    verify_diff = make_verify_diff(
        compile_fn=compile_fn,
        compare_fn=compare,
        workspace=workspace,
        sizes=sizes,
        runs=runs,
        seed=seed,
    )

    findings = detect(target_path)
    code = target_path.read_text(encoding="utf-8")
    reports: list[VerifyReport] = []

    for finding in findings:
        drafts = proposer.propose(finding, code)
        for draft in drafts:
            cand_seed = f"{finding.id}|{draft.diff}".encode()
            cand_id = hashlib.sha256(cand_seed).hexdigest()[:16]
            report = verify_diff(source_dir, main_file, draft.diff, cand_id)
            reports.append(report)

    return reports
