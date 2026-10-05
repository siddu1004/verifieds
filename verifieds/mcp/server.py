"""MCP server implementation using official Python MCP SDK (FastMCP)."""

import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from verifieds.detector.engine import analyze_file as detector_analyze_file
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import Candidate, VerifyReport

ROOT = Path(__file__).resolve().parent.parent.parent


def get_workspace_root() -> Path:
    """Read VERIFIEDS_WORKSPACE from env, defaulting to repo root."""
    env_ws = os.environ.get("VERIFIEDS_WORKSPACE")
    if env_ws:
        return Path(env_ws).resolve()
    return ROOT.resolve()


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


def validate_workspace_path(file_path: str, workspace_root: Path | None = None) -> Path:
    """Validate that file_path resolves within the workspace root."""
    ws = (workspace_root or get_workspace_root()).resolve()
    p = Path(file_path)
    resolved = (ws / p).resolve() if not p.is_absolute() else p.resolve()

    try:
        resolved.relative_to(ws)
    except ValueError as err:
        raise ValueError(
            f"Path escape attempt blocked: {file_path} is outside workspace {ws}"
        ) from err

    if not resolved.exists():
        raise FileNotFoundError(f"File not found within workspace: {resolved}")

    return resolved


def verify_candidate(
    project_dir: str,
    main_file: str,
    diff: str,
    candidate_id: str,
    workload_cmd: str | None = None,
) -> dict[str, Any]:
    ws = get_workspace_root()
    proj_path = validate_workspace_path(project_dir, ws)
    _ = validate_workspace_path(str(Path(project_dir) / main_file), ws)

    import tempfile
    from verifieds.wiring import build_verify_diff

    with tempfile.TemporaryDirectory(dir=ws) as tmpdir:
        verify_fn = build_verify_diff(
            workspace=Path(tmpdir),
            sizes=(200, 2000, 8000),
            runs=3,
        )
        report = verify_fn(
            proj_path,
            main_file,
            diff,
            candidate_id,
            workload_cmd=workload_cmd,
        )
        return report.model_dump()


def create_mcp_server(
    proposer: OllamaProposer | None = None,
    orig_cmd: list[str] | None = None,
) -> FastMCP:
    """Create and configure FastMCP server instance with registered tools."""
    server = FastMCP("VerifiedDS")
    prop_client = proposer or OllamaProposer()
    _ = orig_cmd

    @server.tool(
        name="analyze_file",
        description="Scan C++ source file for bottlenecks.",
    )
    def analyze_file(file_path: str) -> list[dict[str, Any]]:
        target_path = validate_workspace_path(file_path)
        findings = detector_analyze_file(target_path)
        return [f.model_dump() for f in findings]

    @server.tool(
        name="propose_candidates",
        description="Propose candidate drafts for a detected finding.",
    )
    def propose_candidates(file_path: str, finding_id: str) -> list[dict[str, Any]]:
        target_path = validate_workspace_path(file_path)
        findings = detector_analyze_file(target_path)
        target_finding = next((f for f in findings if f.id == finding_id), None)

        if target_finding is None:
            raise ValueError(f"Unknown finding id '{finding_id}' in {file_path}")

        code = target_path.read_text(encoding="utf-8")
        drafts = prop_client.propose(target_finding, code)

        candidates: list[dict[str, Any]] = []
        for idx, draft in enumerate(drafts):
            cand = Candidate(
                id=f"cand_{target_finding.id}_{idx + 1}",
                finding_id=target_finding.id,
                strategy=draft.strategy,
                diff=draft.diff,
                expected_complexity_after=draft.expected_complexity_after,
                risks=draft.risks,
            )
            candidates.append(cand.model_dump())

        return candidates

    @server.tool(
        name="verify_candidate",
        description="Run benchmark harness to verify output equivalence.",
    )
    def verify_candidate_tool(
        project_dir: str,
        main_file: str,
        diff: str,
        candidate_id: str,
        workload_cmd: str | None = None,
    ) -> dict[str, Any]:
        return verify_candidate(
            project_dir, main_file, diff, candidate_id, workload_cmd=workload_cmd
        )

    @server.tool(
        name="explain_change",
        description="Narrative explanation using ONLY numbers present in report.",
    )
    def explain_change(report: dict[str, Any]) -> dict[str, Any]:
        vr = VerifyReport.model_validate(report)
        if not vr.equivalent:
            explanation = (
                f"Candidate {vr.candidate_id} was rejected. "
                f"Reason: {vr.rejected_reason}."
            )
            return {"explanation": explanation, "numbers_used": []}

        speedup_val = vr.speedup_at_max_n
        crossover_val = vr.crossover_n
        numbers: list[float | int] = []

        explanation_parts = [f"Candidate {vr.candidate_id} was verified equivalent."]
        if speedup_val is not None:
            explanation_parts.append(
                f"Achieved speedup at max n of {speedup_val:.2f}x."
            )
            numbers.append(speedup_val)
        if crossover_val is not None:
            explanation_parts.append(f"Crossover observed at n = {crossover_val}.")
            numbers.append(crossover_val)

        for wl in vr.workloads:
            explanation_parts.append(
                f"At n={wl.n}: orig {wl.original_ms_median:.2f} ms "
                f"vs cand {wl.candidate_ms_median:.2f} ms."
            )
            numbers.extend([wl.n, wl.original_ms_median, wl.candidate_ms_median])

        return {
            "explanation": " ".join(explanation_parts),
            "numbers_used": numbers,
        }

    return server


mcp_server = create_mcp_server()

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
