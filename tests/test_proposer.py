"""Unit tests for Ollama proposer client (S-07)."""

from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from typing import Any
import pytest

from verifieds.schemas.models import Finding
from verifieds.proposer.client import OllamaProposer, OllamaParseError, OllamaConfig


class FakeOllamaHandler(BaseHTTPRequestHandler):
    """Fake Ollama HTTP endpoint for testing."""

    responses: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802
        if not FakeOllamaHandler.responses:
            self.send_response(500)
            self.end_headers()
            return

        resp_payload = FakeOllamaHandler.responses.pop(0)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp_payload).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress stdout logging in tests."""
        pass


@pytest.fixture
def fake_ollama_server() -> Generator[str, None, None]:
    """Start an in-test fake Ollama HTTP server on a random free port."""
    server = HTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{host}:{port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        id="find_01",
        rule_id="array-queue-front-removal",
        file="sim/src/queue.cpp",
        start_line=10,
        end_line=20,
        adt="queue",
        impl="ArrayQueue",
        complexity_before="O(n)",
        evidence="pop_front shifts memory linear scan",
    )


def test_proposer_valid_response(
    fake_ollama_server: str, sample_finding: Finding
) -> None:
    """Fake Ollama returning valid JSON candidates."""
    valid_cand_json = json.dumps(
        [
            {
                "id": "cand_01",
                "finding_id": "find_01",
                "strategy": "circular buffer",
                "diff": "--- a/queue.cpp\n+++ b/queue.cpp",
                "expected_complexity_after": "O(1)",
                "risks": ["extra head index tracking"],
            }
        ]
    )

    FakeOllamaHandler.responses = [{"response": valid_cand_json}]

    config = OllamaConfig(base_url=fake_ollama_server, model="qwen2.5-coder")
    proposer = OllamaProposer(config=config)

    candidates = proposer.propose(sample_finding, code_snippet="void pop() {}")
    assert len(candidates) == 1
    assert candidates[0].id == "cand_01"
    assert candidates[0].expected_complexity_after == "O(1)"


def test_proposer_retry_on_malformed_then_succeed(
    fake_ollama_server: str, sample_finding: Finding
) -> None:
    """Retry once if first response is malformed JSON."""
    valid_cand_json = json.dumps(
        [
            {
                "id": "cand_02",
                "finding_id": "find_01",
                "strategy": "heap",
                "diff": "--- a/queue.cpp\n+++ b/queue.cpp",
                "expected_complexity_after": "O(log n)",
                "risks": [],
            }
        ]
    )

    FakeOllamaHandler.responses = [
        {"response": "this is not JSON {bad"},
        {"response": valid_cand_json},
    ]

    config = OllamaConfig(base_url=fake_ollama_server, model="codellama")
    proposer = OllamaProposer(config=config)

    candidates = proposer.propose(sample_finding, code_snippet="void pop() {}")
    assert len(candidates) == 1
    assert candidates[0].id == "cand_02"


def test_proposer_malformed_twice_raises_typed_error(
    fake_ollama_server: str, sample_finding: Finding
) -> None:
    """Fail after one retry if both responses are malformed JSON."""
    FakeOllamaHandler.responses = [
        {"response": "not json 1"},
        {"response": "not json 2"},
    ]

    config = OllamaConfig(base_url=fake_ollama_server, model="custom-model")
    proposer = OllamaProposer(config=config)

    with pytest.raises(OllamaParseError):
        proposer.propose(sample_finding, code_snippet="void pop() {}")


def test_proposer_dict_wrapped_candidates(
    fake_ollama_server: str, sample_finding: Finding
) -> None:
    """Ollama returning dict wrapper with 'candidates' key."""
    dict_resp = json.dumps(
        {
            "candidates": [
                {
                    "id": "cand_dict",
                    "finding_id": "find_01",
                    "strategy": "vector",
                    "diff": "--- a/q\n+++ b/q",
                    "expected_complexity_after": "O(1)",
                    "risks": [],
                }
            ]
        }
    )
    FakeOllamaHandler.responses = [{"response": dict_resp}]
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    cands = proposer.propose(sample_finding, "code")
    assert len(cands) == 1
    assert cands[0].id == "cand_dict"


def test_proposer_non_container_json_raises_parse_error(
    fake_ollama_server: str, sample_finding: Finding
) -> None:
    """Ollama returning a primitive JSON type like number or boolean."""
    FakeOllamaHandler.responses = [{"response": "12345"}, {"response": "true"}]
    proposer = OllamaProposer(OllamaConfig(base_url=fake_ollama_server))
    with pytest.raises(OllamaParseError):
        proposer.propose(sample_finding, "code")


def test_proposer_http_connection_failure(sample_finding: Finding) -> None:
    """Ollama endpoint connection failure triggers OllamaParseError."""
    config = OllamaConfig(base_url="http://127.0.0.1:59999", timeout_seconds=1.0)
    proposer = OllamaProposer(config=config)
    with pytest.raises(OllamaParseError):
        proposer.propose(sample_finding, "code")


def test_proposer_default_config() -> None:
    """Default OllamaConfig parameters."""
    proposer = OllamaProposer()
    assert proposer.config.base_url == "http://localhost:11434"
    assert proposer.config.model == "qwen2.5-coder"
