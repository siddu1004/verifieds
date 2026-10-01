"""Ollama HTTP client for proposal generation."""

import json
from pathlib import Path
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any

from verifieds.schemas.models import Finding, Candidate


class OllamaParseError(Exception):
    """Raised when Ollama output cannot be parsed as valid Candidate JSON."""

    pass


@dataclass(frozen=True)
class OllamaConfig:
    """Configuration for local Ollama HTTP client."""

    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder"
    timeout_seconds: float = 30.0


def _load_prompt_template(name: str) -> str:
    """Load prompt template text from prompts directory."""
    prompts_dir = Path(__file__).parent / "prompts"
    prompt_file = prompts_dir / f"{name}.txt"
    return prompt_file.read_text(encoding="utf-8").strip()


class OllamaProposer:
    """Proposer client interacting with local Ollama model."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()
        self.system_prompt = _load_prompt_template("proposer")

    def _post_generate(self, prompt: str) -> str:
        """Send POST request to Ollama /api/generate endpoint."""
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": self.system_prompt,
            "stream": False,
            "format": "json",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                req, timeout=self.config.timeout_seconds
            ) as resp:
                resp_bytes = resp.read()
                resp_json: dict[str, Any] = json.loads(resp_bytes.decode("utf-8"))
                return str(resp_json.get("response", ""))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            raise OllamaParseError(f"HTTP request to Ollama failed: {err}") from err

    def _parse_candidates(self, response_text: str) -> list[Candidate]:
        """Parse raw response text into list of Candidate objects."""
        try:
            raw_data = json.loads(response_text)
        except json.JSONDecodeError as err:
            raise OllamaParseError(f"Invalid JSON string from Ollama: {err}") from err

        if isinstance(raw_data, dict):
            # Model might wrap array in {"candidates": [...]}
            raw_list = raw_data.get("candidates", [raw_data])
        elif isinstance(raw_data, list):
            raw_list = raw_data
        else:
            raise OllamaParseError("JSON response must be a list or dict")

        candidates: list[Candidate] = []
        for item in raw_list:
            try:
                cand = Candidate.model_validate(item)
                candidates.append(cand)
            except Exception as err:
                raise OllamaParseError(
                    f"Failed to validate Candidate item: {err}"
                ) from err

        return candidates

    def propose(self, finding: Finding, code_snippet: str) -> list[Candidate]:
        """Generate candidate proposed rewrites for a finding.

        Retries once if response text cannot be parsed as valid Candidates JSON.
        """
        prompt = (
            f"Finding ID: {finding.id}\n"
            f"ADT: {finding.adt}\n"
            f"Impl: {finding.impl}\n"
            f"Evidence: {finding.evidence}\n"
            f"Complexity Before: {finding.complexity_before}\n"
            f"Code:\n<code>\n{code_snippet}\n</code>"
        )

        attempts = 2
        last_error: Exception | None = None

        for _ in range(attempts):
            raw_response = self._post_generate(prompt)
            try:
                return self._parse_candidates(raw_response)
            except OllamaParseError as err:
                last_error = err

        raise OllamaParseError(
            f"Failed to obtain valid Candidate JSON after {attempts} attempts. "
            f"Last error: {last_error}"
        )
