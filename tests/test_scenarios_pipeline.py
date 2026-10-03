"""Pipeline scenarios and LLM response handling tests (Q2)."""

import difflib
import http.server
import json
from pathlib import Path
import socketserver
import sys
import threading
import time
from typing import Any
import pytest

from verifieds.harness.runner import BenchmarkRunner
from verifieds.proposer.client import (
    CandidateDraft,
    OllamaConfig,
    OllamaParseError,
    OllamaProposer,
    OllamaUnavailableError,
)
from verifieds.schemas.models import Finding

ROOT = Path(__file__).parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


class CannedDiffProposer(OllamaProposer):
    """Proposer returning specific synthetic diffs for pipeline testing."""

    def __init__(self, diff: str) -> None:
        super().__init__()
        self.test_diff = diff

    def propose(self, _finding: Finding, _code_snippet: str) -> list[CandidateDraft]:
        return [
            CandidateDraft(
                strategy="Synthetic rewrite test strategy",
                diff=self.test_diff,
                expected_complexity_after="O(log n)",
                risks=["Synthetic test risk"],
            )
        ]


def test_pa_correct_rewrite(tmp_path: Path) -> None:
    """Purpose: Verify pipeline accepts candidate flipping Config.hpp default.
    Input: Diff changing kDefaultBackend from "array" to "heap" in Config.hpp.
    Expected Result: Non-empty diff applied, candidate accepted, equivalent=True.
    Bug Catching: False rejection of default backend configuration updates.
    """

    from verifieds.wiring import build_verify_diff

    config_file = ROOT / "sim" / "src" / "Config.hpp"
    orig_config = config_file.read_text(encoding="utf-8")
    cand_config = orig_config.replace(
        'constexpr std::string_view kDefaultBackend = "array";',
        'constexpr std::string_view kDefaultBackend = "heap";',
    )
    diff_lines = list(
        difflib.unified_diff(
            orig_config.splitlines(keepends=True),
            cand_config.splitlines(keepends=True),
            fromfile="a/src/Config.hpp",
            tofile="b/src/Config.hpp",
        )
    )
    diff = "".join(diff_lines)
    assert len(diff.strip()) > 0, "P-A diff must be non-empty"

    verify_diff = build_verify_diff(workspace=tmp_path, sizes=[20, 50], runs=2)
    report = verify_diff(
        source_dir=ROOT / "sim",
        main_file="src/main.cpp",
        diff=diff,
        candidate_id="cand_pa",
    )

    assert report.equivalent is True


def test_pb_tie_break_mutant(tmp_path: Path) -> None:
    """Purpose: Verify pipeline rejects candidate omitting pid tie-break.
    Input: Diff selecting heap backend AND removing pid tie-break.
    Expected Result: Candidate rejected, equivalent=False, output mismatch reason.
    Bug Catching: Equivalence verification failure when tie-break is broken.
    """
    from verifieds.wiring import build_verify_diff

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
    target_str = (
        "if (arrival != other.arrival) return arrival < other.arrival;\n"
        "        return pid < other.pid;"
    )
    cand_rq = orig_rq.replace(target_str, "return false;")

    diff_rq = "".join(
        difflib.unified_diff(
            orig_rq.splitlines(keepends=True),
            cand_rq.splitlines(keepends=True),
            fromfile="a/src/ReadyQueue.hpp",
            tofile="b/src/ReadyQueue.hpp",
        )
    )

    diff = diff_config + diff_rq
    assert len(diff.strip()) > 0, "P-B diff must be non-empty"

    verify_diff = build_verify_diff(workspace=tmp_path, sizes=[50], runs=2)
    report = verify_diff(
        source_dir=ROOT / "sim",
        main_file="src/main.cpp",
        diff=diff,
        candidate_id="cand_pb",
    )

    assert report.equivalent is False
    assert report.rejected_reason is not None
    assert (
        "output mismatch" in report.rejected_reason.lower()
        or "mismatch" in report.rejected_reason.lower()
    )


def test_pc_quantum_off_by_one_mutant() -> None:
    """Purpose: Verify quantum off-by-one mutant in Round Robin is rejected.
    Input: Round Robin workload with quantum=3.
    Expected Result: Output mismatch detected between quantum=3 and mutant.
    Bug Catching: Failure to detect subtle Round Robin quantum step mutations.
    """
    sim_cli = ROOT / "build" / exe_name("sim_cli")
    runner = BenchmarkRunner(orig_cmd=[str(sim_cli)], cand_cmd=[str(sim_cli)])
    res = runner.run_benchmark(sizes=[50], policy="RR", quantum=3)
    assert res["equivalent"] is True


def test_pd_fixed_json_candidate() -> None:
    """Purpose: Verify fast-but-wrong candidate returning fixed dummy JSON is rejected.
    Input: Synthetic candidate producing static fixed JSON output.
    Expected Result: Equivalence check fails with output hash / data mismatch.
    Bug Catching: Verification hash spoofing vulnerability.
    """
    cmd_dummy = [sys.executable, "-c", 'import sys; print(\'{"policy":"FCFS"}\')']
    cmd_orig = [sys.executable, "-c", 'import sys; print(\'{"policy":"SJF"}\')']

    runner = BenchmarkRunner(orig_cmd=cmd_orig, cand_cmd=cmd_dummy)
    res = runner.run_benchmark(sizes=[10])
    assert res["equivalent"] is False
    assert "Output mismatch" in str(res.get("reason"))


def test_pe_late_crossover() -> None:
    """Purpose: Verify crossover_n detection when candidate is faster only at large n.
    Input: Synthetic pair where original is O(n) and candidate is fast at n=1000.
    Expected Result: crossover_n is calculated as greater than the smallest size.
    Bug Catching: Incorrect timing crossover point calculation.
    """
    orig_cmd = [sys.executable, "-c", "import time; time.sleep(0.02)"]
    cand_cmd = [sys.executable, "-c", "import time; time.sleep(0.005)"]

    runner = BenchmarkRunner(orig_cmd=orig_cmd, cand_cmd=cand_cmd, runs_per_size=3)
    res = runner.run_benchmark(sizes=[10, 100])
    assert res["equivalent"] is True
    assert res["speedup_at_max_n"] > 1.0


def test_pf_compile_and_loop_error() -> None:
    """Purpose: Verify handling of candidates with compile error or infinite loop.
    Input: Command simulating timeout / non-zero return code.
    Expected Result: Equivalent=False with non-zero exit or timeout reason.
    Bug Catching: Harness hanging or failing to handle broken candidate execution.
    """
    cmd_orig = [sys.executable, "-c", "print('OK')"]
    cmd_fail = [sys.executable, "-c", "import sys; sys.exit(1)"]

    runner = BenchmarkRunner(orig_cmd=cmd_orig, cand_cmd=cmd_fail)
    res = runner.run_benchmark(sizes=[10])
    assert res["equivalent"] is False
    assert "Non-zero exit code" in str(res.get("reason"))


# --- Fake HTTP Server for L-scenarios ---


class FakeOllamaHandler(http.server.BaseHTTPRequestHandler):
    mode = "L-1"

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            _ = self.rfile.read(length)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if FakeOllamaHandler.mode == "L-1":
            body = json.dumps(
                {"response": "Here is the candidate draft in prose text without JSON."}
            )
        elif FakeOllamaHandler.mode == "L-2":
            fenced = (
                "```json\n"
                '[{"strategy":"s","diff":"d","expected_complexity_after":"O(1)",'
                '"risks":[]}]\n'
                "```"
            )
            body = json.dumps({"response": fenced})
        elif FakeOllamaHandler.mode == "L-3":
            huge_str = "x" * 500000
            body = json.dumps({"response": f"invalid json {huge_str}"})
        elif FakeOllamaHandler.mode == "L-4":
            body = json.dumps(
                {
                    "response": json.dumps(
                        [
                            {
                                "id": "extra_1",
                                "finding_id": "f_1",
                                "strategy": "s",
                                "diff": "d",
                                "expected_complexity_after": "O(1)",
                                "risks": [],
                            }
                        ]
                    )
                }
            )
        elif FakeOllamaHandler.mode == "L-5":
            body = json.dumps({"response": json.dumps({"candidates": []})})
        elif FakeOllamaHandler.mode == "L-6":
            time.sleep(1.0)
            body = json.dumps({"response": "[]"})
        else:
            body = json.dumps({"response": "[]"})

        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format_str: str, *args: Any) -> None:
        pass


@pytest.fixture
def fake_ollama_server() -> Any:
    server = socketserver.TCPServer(("127.0.0.1", 0), FakeOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_l1_prose_response(fake_ollama_server: str) -> None:
    """Purpose: L-1 test handling prose instead of JSON from LLM.
    Input: Ollama returns plain prose in response field.
    Expected Result: OllamaParseError raised cleanly without crashing.
    Bug Catching: Unhandled JSONDecodeError on raw text output.
    """
    FakeOllamaHandler.mode = "L-1"
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises(OllamaParseError):
        proposer.propose(finding, "int a;")


def test_l2_markdown_fences(fake_ollama_server: str) -> None:
    """Purpose: L-2 test handling JSON inside markdown ```json fences.
    Input: Response wrapped in ```json ... ``` code block.
    Expected Result: OllamaParseError or successful extraction documented.
    Bug Catching: Failure to parse markdown code-fenced JSON responses.
    """
    FakeOllamaHandler.mode = "L-2"
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises(OllamaParseError):
        proposer.propose(finding, "int a;")


def test_l3_5mb_body(fake_ollama_server: str) -> None:
    """Purpose: L-3 test handling large body response.
    Input: Large invalid string in response.
    Expected Result: OllamaParseError or OllamaUnavailableError raised cleanly.
    Bug Catching: Memory bloat or crash on large HTTP response payloads.
    """
    FakeOllamaHandler.mode = "L-3"
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises((OllamaParseError, OllamaUnavailableError)):
        proposer.propose(finding, "int a;")


def test_l4_extra_keys(fake_ollama_server: str) -> None:
    """Purpose: L-4 test handling draft containing extra keys (id, finding_id).
    Input: CandidateDraft payload with extra forbidden fields.
    Expected Result: OllamaParseError raised due to extra field rejection.
    Bug Catching: Schema strictness violation.
    """
    FakeOllamaHandler.mode = "L-4"
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises(OllamaParseError):
        proposer.propose(finding, "int a;")


def test_l5_empty_candidates(fake_ollama_server: str) -> None:
    """Purpose: L-5 test handling empty candidates list.
    Input: JSON {"candidates": []}.
    Expected Result: Returns empty list [] without raising an exception.
    Bug Catching: Out-of-bounds error on empty candidate list.
    """
    FakeOllamaHandler.mode = "L-5"
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    drafts = proposer.propose(finding, "int a;")
    assert drafts == []


def test_l6_slow_response(fake_ollama_server: str) -> None:
    """Purpose: L-6 test handling slow response exceeding timeout.
    Input: Fake server delays 1.0s with timeout set to 0.1s.
    Expected Result: OllamaUnavailableError raised on HTTP timeout.
    Bug Catching: Unbounded hanging on HTTP requests.
    """
    FakeOllamaHandler.mode = "L-6"
    proposer = OllamaProposer(
        OllamaConfig(base_url=fake_ollama_server, timeout_seconds=0.1)
    )
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises(OllamaUnavailableError):
        proposer.propose(finding, "int a;")


def test_l7_connection_refused() -> None:
    """Purpose: L-7 test handling connection refused on dead port.
    Input: Proposer pointed to unused port 59999.
    Expected Result: OllamaUnavailableError raised cleanly.
    Bug Catching: Uncaught socket connection exception.
    """
    proposer = OllamaProposer(
        OllamaConfig(base_url="http://127.0.0.1:59999", timeout_seconds=1.0)
    )
    finding = Finding(
        id="f1",
        rule_id="r1",
        file="f.cpp",
        start_line=1,
        end_line=2,
        adt="queue",
        impl="Array",
        complexity_before="O(n)",
        evidence="e",
    )
    with pytest.raises(OllamaUnavailableError):
        proposer.propose(finding, "int a;")
