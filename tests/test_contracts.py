"""Pins the real proposer to the lane contract.

Purpose: parallel lanes code against verifieds.contracts; this fails if the real
OllamaProposer drifts from the Proposer protocol's call shape.
"""

import inspect

from verifieds import contracts
from verifieds.proposer.client import OllamaProposer


def test_ollama_proposer_matches_contract() -> None:
    expected = inspect.signature(contracts.Proposer.propose)
    actual = inspect.signature(OllamaProposer.propose)
    assert list(actual.parameters) == list(expected.parameters)
    assert actual.return_annotation == expected.return_annotation
