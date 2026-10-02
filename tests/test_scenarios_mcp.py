"""MCP scenario end-to-end scripted session and security error tests (Q3)."""

import asyncio
import json
from pathlib import Path
from typing import Any
import pytest

from verifieds.mcp.server import create_mcp_server, validate_workspace_path
from verifieds.proposer.client import CandidateDraft, OllamaProposer
from verifieds.schemas.models import Candidate, Finding, VerifyReport

ROOT = Path(__file__).parent.parent


def get_tool_data(res: Any) -> Any:
    """Extract tool result data payload from FastMCP call_tool return value."""
    data = res[1] if isinstance(res, tuple) else res
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


class FakeMCPProposer(OllamaProposer):
    """Fake proposer returning P-A heap rewrite candidate draft."""

    def propose(self, _finding: Finding, _code_snippet: str) -> list[CandidateDraft]:
        diff = (
            "--- ReadyQueue.hpp\n"
            "+++ ReadyQueue.hpp\n"
            "@@ -10,1 +10,1 @@\n"
            '-constexpr std::string_view kDefaultBackend = "array";\n'
            '+constexpr std::string_view kDefaultBackend = "heap";\n'
        )
        return [
            CandidateDraft(
                strategy="HeapReadyQueue priority queue optimization",
                diff=diff,
                expected_complexity_after="O(log n)",
                risks=["Minimal memory overhead"],
            )
        ]


def test_mcp_scripted_session() -> None:
    """Purpose: Scripted end-to-end MCP tool chain execution.
    Input: Target C++ header sim/src/ReadyQueue.hpp.
    Expected Result: All tool outputs validate against schemas.
    Bug Catching: Contract drift between MCP tools and Pydantic schemas.
    """
    proposer = FakeMCPProposer()
    sim_cli = (
        ROOT / "build" / "sim_cli.exe"
        if ROOT.joinpath("build/sim_cli.exe").exists()
        else ROOT / "build" / "sim_cli"
    )
    orig_cmd = [str(sim_cli)]

    server = create_mcp_server(proposer=proposer, orig_cmd=orig_cmd)

    async def run_session() -> None:
        # Step 1: analyze_file
        res_analyze = await server.call_tool(
            "analyze_file", {"file_path": "sim/src/ReadyQueue.hpp"}
        )
        findings_raw = get_tool_data(res_analyze)
        assert isinstance(findings_raw, list)
        assert len(findings_raw) >= 1
        finding_obj = Finding.model_validate(findings_raw[0])

        schema_finding = json.loads(
            (ROOT / "schemas" / "finding.json").read_text(encoding="utf-8")
        )
        assert finding_obj.model_dump() is not None
        assert "properties" in schema_finding

        # Step 2: propose_candidates
        res_propose = await server.call_tool(
            "propose_candidates",
            {"file_path": "sim/src/ReadyQueue.hpp", "finding_id": finding_obj.id},
        )
        cands_raw = get_tool_data(res_propose)
        assert isinstance(cands_raw, list)
        assert len(cands_raw) >= 1
        cand_obj = Candidate.model_validate(cands_raw[0])

        schema_cand = json.loads(
            (ROOT / "schemas" / "candidate.json").read_text(encoding="utf-8")
        )
        assert cand_obj.model_dump() is not None
        assert "properties" in schema_cand

        # Step 3: verify_candidate
        res_verify = await server.call_tool(
            "verify_candidate",
            {"candidate_id": cand_obj.id, "file_path": "sim/src/ReadyQueue.hpp"},
        )
        report_raw = get_tool_data(res_verify)
        report_obj = VerifyReport.model_validate(report_raw)

        schema_report = json.loads(
            (ROOT / "schemas" / "verify_report.json").read_text(encoding="utf-8")
        )
        assert report_obj.model_dump() is not None
        assert "properties" in schema_report

        # Step 4: explain_change
        res_explain = await server.call_tool("explain_change", {"report": report_raw})
        explain_data = get_tool_data(res_explain)
        explanation = explain_data["explanation"]
        numbers_used = explain_data["numbers_used"]

        assert isinstance(explanation, str)
        report_str = json.dumps(report_raw)
        for num in numbers_used:
            assert str(num) in report_str or f"{num:.2f}" in explanation

    asyncio.run(run_session())


def test_mcp_error_scenarios() -> None:
    """Purpose: Security boundary and error scenario verification.
    Input: Path escape attempts, unknown finding IDs, non-existent files.
    Expected Result: Blocked with clean ValueError, FileNotFoundError, or ToolError.
    Bug Catching: Path traversal vulnerabilities and unhandled input exceptions.
    """
    server = create_mcp_server()

    async def run_errors() -> None:
        # Path escape (relative ..)
        with pytest.raises(ValueError, match="Path escape attempt blocked"):
            validate_workspace_path("../../outside.cpp")

        # Path escape (absolute outside)
        from tests.test_safety import get_outside_workspace_path

        with pytest.raises(ValueError, match="Path escape attempt blocked"):
            validate_workspace_path(get_outside_workspace_path())

        # Unknown finding id
        with pytest.raises(Exception, match="Unknown finding id"):
            await server.call_tool(
                "propose_candidates",
                {
                    "file_path": "sim/src/ReadyQueue.hpp",
                    "finding_id": "non_existent_id_999",
                },
            )

        # File not found within workspace
        with pytest.raises(FileNotFoundError):
            validate_workspace_path("sim/src/DoesNotExist.hpp")

    asyncio.run(run_errors())
