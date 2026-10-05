"""Tests for the verifieds.wiring module."""

from pathlib import Path
from verifieds.wiring import default_detect, build_verify_diff


def test_wiring_default_detect() -> None:
    """Test default_detect function binding."""
    findings = default_detect(Path("sim/src/ReadyQueue.hpp"))
    assert isinstance(findings, list)


def test_wiring_build_verify_diff(tmp_path: Path) -> None:
    """Test build_verify_diff returning a VerifyDiffFn callable."""
    verify_diff = build_verify_diff(workspace=tmp_path, sizes=[10])
    assert callable(verify_diff)
