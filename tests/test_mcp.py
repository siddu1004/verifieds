"""Tests for verifieds.mcp server and entry point (MCP-1 / MCP-2 / R-09)."""

import asyncio
import difflib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
import pytest

from verifieds.mcp.server import (
    create_mcp_server,
    get_workspace_root,
    validate_workspace_path,
)
from verifieds.proposer.client import OllamaProposer
from verifieds.schemas.models import (
    CandidateDraft,
    Finding,
    VerifyReport,
)

ROOT = Path(__file__).resolve().parent.parent


class FakeProposer(OllamaProposer):
    def __init__(self, drafts: list[CandidateDraft]) -> None:
        super().__init__()
        self._drafts = drafts

    def propose(self, finding: Finding, code: str) -> list[CandidateDraft]:
        _ = (finding, code)
        return self._drafts


def test_path_escape_rejection(tmp_path: Path) -> None:
    outside_file = tmp_path / "outside.cpp"
    outside_file.write_text("int main(){}", encoding="utf-8")

    with pytest.raises(ValueError, match="Path escape attempt blocked"):
        validate_workspace_path(str(outside_file))

    with pytest.raises(ValueError, match="Path escape attempt blocked"):
        validate_workspace_path("../outside.cpp")


def test_workspace_root_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom_ws = tmp_path / "my_project"
    custom_ws.mkdir()
    inside_file = custom_ws / "main.cpp"
    inside_file.write_text("int main() {}", encoding="utf-8")

    monkeypatch.setenv("VERIFIEDS_WORKSPACE", str(custom_ws))
    assert get_workspace_root() == custom_ws.resolve()

    res = validate_workspace_path("main.cpp")
    assert res == inside_file.resolve()

    # File outside custom_ws (e.g. repo sim directory) should be rejected
    with pytest.raises(ValueError, match="Path escape attempt blocked"):
        validate_workspace_path(str(ROOT / "sim" / "src" / "main.cpp"))


def get_tool_data(res: Any) -> Any:
    data = res[1] if isinstance(res, tuple) else res
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def make_pa_diff() -> str:
    config_file = ROOT / "sim" / "src" / "Config.hpp"
    orig_config = config_file.read_text(encoding="utf-8")
    cand_config = orig_config.replace(
        'constexpr std::string_view kDefaultBackend = "array";',
        'constexpr std::string_view kDefaultBackend = "heap";',
    )
    return "".join(
        difflib.unified_diff(
            orig_config.splitlines(keepends=True),
            cand_config.splitlines(keepends=True),
            fromfile="a/src/Config.hpp",
            tofile="b/src/Config.hpp",
        )
    )


def make_pb_diff() -> str:
    config_file = ROOT / "sim" / "src" / "Config.hpp"
    orig_config = config_file.read_text(encoding="utf-8")
    cand_config = orig_config.replace(
        'constexpr std::string_view kDefaultBackend = "array";',
        'constexpr std::string_view kDefaultBackend = "heap";',
    )
    diff_config = "".join(
        difflib.unified_diff(
            orig_config.splitlines(keepends=True),
            cand_config.splitlines(keepends=True),
            fromfile="a/src/Config.hpp",
            tofile="b/src/Config.hpp",
        )
    )

    rq_file = ROOT / "sim" / "src" / "ReadyQueue.hpp"
    orig_rq = rq_file.read_text(encoding="utf-8")
    cand_rq = orig_rq.replace("return pid < other.pid;", "return false;")
    diff_rq = "".join(
        difflib.unified_diff(
            orig_rq.splitlines(keepends=True),
            cand_rq.splitlines(keepends=True),
            fromfile="a/src/ReadyQueue.hpp",
            tofile="b/src/ReadyQueue.hpp",
        )
    )

    return diff_config + "\n" + diff_rq


def test_mcp_tools_in_process() -> None:
    async def run_test() -> None:
        pa_diff = make_pa_diff()
        draft = CandidateDraft(
            strategy="Min heap queue",
            diff=pa_diff,
            expected_complexity_after="O(log n)",
            risks=[],
        )
        fake_proposer = FakeProposer([draft])

        server = create_mcp_server(proposer=fake_proposer)

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
        cand_id = cand_dict["id"]

        # 3. verify_candidate (P-A diff: equivalent True)
        res3 = await server.call_tool(
            "verify_candidate",
            {
                "project_dir": "sim",
                "main_file": "src/main.cpp",
                "diff": pa_diff,
                "candidate_id": cand_id,
            },
        )
        report_raw = get_tool_data(res3)
        assert isinstance(report_raw, dict)
        vr = VerifyReport.model_validate(report_raw)
        assert vr.equivalent is True

        # 4. verify_candidate (P-B diff: equivalent False with output mismatch)
        pb_diff = make_pb_diff()
        res_pb = await server.call_tool(
            "verify_candidate",
            {
                "project_dir": "sim",
                "main_file": "src/main.cpp",
                "diff": pb_diff,
                "candidate_id": "cand_pb_1",
            },
        )
        report_pb = VerifyReport.model_validate(get_tool_data(res_pb))
        assert report_pb.equivalent is False
        assert report_pb.rejected_reason is not None
        assert "Output mismatch" in report_pb.rejected_reason

        # 5. verify_candidate (Invalid patch)
        res_invalid = await server.call_tool(
            "verify_candidate",
            {
                "project_dir": "sim",
                "main_file": "src/main.cpp",
                "diff": "invalid patch header\n-foo\n+bar\n",
                "candidate_id": "cand_bad_patch",
            },
        )
        report_invalid = VerifyReport.model_validate(get_tool_data(res_invalid))
        assert report_invalid.equivalent is False
        assert report_invalid.rejected_reason is not None
        assert "diff does not apply" in report_invalid.rejected_reason

        # 6. verify_candidate (Compile error)
        config_file = ROOT / "sim" / "src" / "Config.hpp"
        orig_config = config_file.read_text(encoding="utf-8")
        cand_config = orig_config.replace(
            'constexpr std::string_view kDefaultBackend = "array";',
            "THIS_IS_SYNTAX_ERROR;",
        )
        compile_err_diff = "".join(
            difflib.unified_diff(
                orig_config.splitlines(keepends=True),
                cand_config.splitlines(keepends=True),
                fromfile="a/src/Config.hpp",
                tofile="b/src/Config.hpp",
            )
        )
        res_compile = await server.call_tool(
            "verify_candidate",
            {
                "project_dir": "sim",
                "main_file": "src/main.cpp",
                "diff": compile_err_diff,
                "candidate_id": "cand_compile_err",
            },
        )
        report_compile = VerifyReport.model_validate(get_tool_data(res_compile))
        assert report_compile.equivalent is False
        assert report_compile.rejected_reason is not None
        assert "Compile error" in report_compile.rejected_reason

        # 7. explain_change
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


def test_generic_cpp_project_verification() -> None:
    async def run_test() -> None:
        proj_dir = ROOT / "build" / "tmp_test_generic_proj"
        proj_dir.mkdir(parents=True, exist_ok=True)

        main_cpp = proj_dir / "main.cpp"
        main_cpp.write_text(
            """#include <iostream>
#include <fstream>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    std::ifstream infile(argv[1]);
    long long val;
    std::vector<long long> nums;
    while (infile >> val) {
        nums.push_back(val);
    }
    long long total = 0;
    for (size_t i = 0; i < nums.size(); ++i) {
        for (size_t j = i; j < nums.size(); ++j) {
            total += nums[j];
        }
    }
    std::cout << total << "\\n";
    return 0;
}
""",
            encoding="utf-8",
        )

        cand_cpp_content = """#include <iostream>
#include <fstream>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc < 2) return 1;
    std::ifstream infile(argv[1]);
    long long val;
    std::vector<long long> nums;
    while (infile >> val) {
        nums.push_back(val);
    }
    long long total = 0;
    for (size_t i = 0; i < nums.size(); ++i) {
        total += nums[i] * (i + 1);
    }
    std::cout << total << "\\n";
    return 0;
}
"""

        diff = "".join(
            difflib.unified_diff(
                main_cpp.read_text(encoding="utf-8").splitlines(keepends=True),
                cand_cpp_content.splitlines(keepends=True),
                fromfile="a/main.cpp",
                tofile="b/main.cpp",
            )
        )

        gen_py = proj_dir / "gen.py"
        gen_py.write_text(
            """import random
import sys
args = sys.argv[1:]
n = int(args[0])
seed = int(args[1])
out_file = args[2]
rng = random.Random(seed)
with open(out_file, "w") as f:
    f.write(" ".join(str(rng.randint(1, 100)) for _ in range(n)))
""",
            encoding="utf-8",
        )

        server = create_mcp_server()
        rel_proj = "build/tmp_test_generic_proj"
        workload_cmd = f'"{sys.executable}" {rel_proj}/gen.py {{n}} {{seed}} {{out}}'

        res = await server.call_tool(
            "verify_candidate",
            {
                "project_dir": rel_proj,
                "main_file": "main.cpp",
                "diff": diff,
                "candidate_id": "c_sum_1",
                "workload_cmd": workload_cmd,
            },
        )
        report_dict = get_tool_data(res)
        report = VerifyReport.model_validate(report_dict)
        assert report.equivalent is True
        assert report.speedup_at_max_n is not None
        assert report.speedup_at_max_n > 1.0

    asyncio.run(run_test())


def test_mcp_stdio_subprocess() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    cmd = [sys.executable, "-m", "verifieds.mcp"]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(ROOT),
    )

    try:
        assert proc.stdin is not None
        assert proc.stdout is not None

        # 1. initialize request
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test_client", "version": "1.0"},
            },
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()

        line1 = proc.stdout.readline()
        resp1 = json.loads(line1)
        assert resp1.get("id") == 1
        assert "result" in resp1

        # 2. notifications/initialized
        init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        proc.stdin.write(json.dumps(init_notif) + "\n")
        proc.stdin.flush()

        # 3. tools/list request
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        proc.stdin.write(json.dumps(list_req) + "\n")
        proc.stdin.flush()

        line2 = proc.stdout.readline()
        resp2 = json.loads(line2)
        assert resp2.get("id") == 2
        tools_list = resp2.get("result", {}).get("tools", [])
        tool_names = {t["name"] for t in tools_list}
        assert "verify_candidate" in tool_names
        assert "analyze_file" in tool_names

    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=5.0)
        assert proc.returncode == 0


def test_mcp_main_module_import() -> None:
    import verifieds.mcp.__main__ as mcp_main

    assert hasattr(mcp_main, "mcp_server")
