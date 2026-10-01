"""Proposer package for LLM candidate generation."""

from verifieds.proposer.client import (
    OllamaProposer,
    OllamaConfig,
    OllamaParseError,
    OllamaUnavailableError,
)

__all__ = [
    "OllamaProposer",
    "OllamaConfig",
    "OllamaParseError",
    "OllamaUnavailableError",
]
