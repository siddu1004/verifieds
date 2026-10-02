"""Tests for verifieds.mcp server."""

import asyncio
import sys
from pathlib import Path
from typing import Any
import pytest
from verifieds.mcp.server import create_mcp_server, validate_workspace_path
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import CandidateDraft, Finding, VerifyReport

ROOT = Path(__file__).resolve().parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


class FakeProposer(OllamaProposer):
    def __init__(self, drafts: list[CandidateDraft]) -> None:
        super().__init__()
        self._drafts = drafts

    def propose(self, finding: Finding, code: str) -> list[CandidateDraft]:
        _ = (finding, code)
        return self._drafts


def test_path_escape_rejection(tmp_path: Path):
    outside_file = tmp_path / "outside.cpp"
    outside_file.write_text("int main(){}", encoding="utf-8")

    with pytest.raises(ValueError, match="Path escape attempt blocked"):
        validate_workspace_path(str(outside_file))

    with pytest.raises(ValueError, match="Path escape attempt blocked"):
        validate_workspace_path("../outside.cpp")


def get_tool_data(res: Any) -> Any:
    data = res[1] if isinstance(res, tuple) else res
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def test_mcp_tools_in_process():
    async def run_test():
        draft = CandidateDraft(
            strategy="Min heap queue",
            diff="--- a\n+++ b\n",
            expected_complexity_after="O(log n)",
            risks=[],
        )
        fake_proposer = FakeProposer([draft])
        sim_cli = ROOT / "build" / exe_name("sim_cli")

        server = create_mcp_server(proposer=fake_proposer, orig_cmd=[str(sim_cli)])

        tools = await server.list_tools()
        tool_names = {t.name for t in tools}
        assert tool_names == {
            "analyze_file",
            "propose_candidates",
            "verify_candidate",
            "explain_change",
        }

        rel_target = "sim/src/ReadyQueue.hpp"

        # 1. analyze_file
        res1 = await server.call_tool("analyze_file", {"file_path": rel_target})
        findings_raw = get_tool_data(res1)
        assert isinstance(findings_raw, list)
        assert len(findings_raw) >= 1
        finding_dict = findings_raw[0]
        Finding.model_validate(finding_dict)

        finding_id = finding_dict["id"]

        # 2. propose_candidates
        res2 = await server.call_tool(
            "propose_candidates", {"file_path": rel_target, "finding_id": finding_id}
        )
        candidates_raw = get_tool_data(res2)
        assert isinstance(candidates_raw, list)
        assert len(candidates_raw) >= 1
        cand_dict = candidates_raw[0]

        # 3. verify_candidate
        cand_id = cand_dict["id"]
        res3 = await server.call_tool(
            "verify_candidate", {"candidate_id": cand_id, "file_path": rel_target}
        )
        report_raw = get_tool_data(res3)
        assert isinstance(report_raw, dict)
        vr = VerifyReport.model_validate(report_raw)
        assert vr.equivalent is True

        # 4. explain_change
        res4 = await server.call_tool("explain_change", {"report": report_raw})
        explanation_raw = get_tool_data(res4)
        assert isinstance(explanation_raw, dict)
        assert "explanation" in explanation_raw
        assert "numbers_used" in explanation_raw

        # Rejection for unknown finding
        with pytest.raises(Exception, match="Unknown finding id"):
            await server.call_tool(
                "propose_candidates",
                {"file_path": rel_target, "finding_id": "unknown_id"},
            )

    asyncio.run(run_test())
