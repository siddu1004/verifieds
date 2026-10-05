import http.server
import json
import os
import socketserver
import threading
from typing import Any
from unittest.mock import patch

from verifieds.doctor import run_doctor


class FakeOllamaHandler(http.server.BaseHTTPRequestHandler):
    models: list[dict[str, Any]] = [{"name": "qwen2.5-coder:latest"}]
    status_code: int = 200

    def do_GET(self) -> None:
        if self.path == "/api/tags":
            self.send_response(self.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = json.dumps({"models": self.models})
            self.wfile.write(payload.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


def test_doctor_all_pass(tmp_path: Any) -> None:
    server = socketserver.TCPServer(("127.0.0.1", 0), FakeOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    url = f"http://127.0.0.1:{port}"
    env = {
        "VERIFIEDS_WORKSPACE": str(tmp_path),
        "VERIFIEDS_OLLAMA_URL": url,
        "VERIFIEDS_OLLAMA_MODEL": "qwen2.5-coder",
    }

    try:
        with patch.dict(os.environ, env):
            code = run_doctor()
            assert code == 0
    finally:
        server.shutdown()
        server.server_close()


def test_doctor_ollama_absent(tmp_path: Any) -> None:
    env = {
        "VERIFIEDS_WORKSPACE": str(tmp_path),
        "VERIFIEDS_OLLAMA_URL": "http://127.0.0.1:59999",
    }

    with patch.dict(os.environ, env):
        code = run_doctor()
        assert code == 1


def test_doctor_model_missing(tmp_path: Any) -> None:
    FakeOllamaHandler.models = [{"name": "llama3:latest"}]
    server = socketserver.TCPServer(("127.0.0.1", 0), FakeOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    url = f"http://127.0.0.1:{port}"
    env = {
        "VERIFIEDS_WORKSPACE": str(tmp_path),
        "VERIFIEDS_OLLAMA_URL": url,
        "VERIFIEDS_OLLAMA_MODEL": "qwen2.5-coder",
    }

    try:
        with patch.dict(os.environ, env):
            code = run_doctor()
            assert code == 1
    finally:
        server.shutdown()
        server.server_close()
        FakeOllamaHandler.models = [{"name": "qwen2.5-coder:latest"}]


def test_doctor_gxx_missing(tmp_path: Any) -> None:
    env = {
        "VERIFIEDS_WORKSPACE": str(tmp_path),
        "VERIFIEDS_OLLAMA_URL": "http://127.0.0.1:59999",
    }
    with (
        patch.dict(os.environ, env),
        patch("shutil.which", return_value=None),
    ):
        code = run_doctor()
        assert code == 1


def test_doctor_main(tmp_path: Any) -> None:
    from verifieds.doctor import main

    env = {
        "VERIFIEDS_WORKSPACE": str(tmp_path),
        "VERIFIEDS_OLLAMA_URL": "http://127.0.0.1:59999",
    }
    with patch.dict(os.environ, env), patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_called_once_with(1)
