"""README validation tests (S-12 / R-10)."""

import importlib.util
import re
from pathlib import Path


def test_readme_contents() -> None:
    """Validate README sections and code snippets."""
    readme_path = Path(__file__).parent.parent / "README.md"
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")
    assert "Quick Start" in content
    assert "MCP Server Registration" in content
    assert "Resource Limits & Safety Disclaimer" in content
    assert "NotImplementedError" in content
    assert "smoke.py` is excluded" in content


def test_readme_modules_exist() -> None:
    """Validate every module command named in README exists as a runnable module."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    matches = re.findall(r"python\s+-m\s+verifieds\.([a-zA-Z0-9_\.]+)", content)
    assert matches, "No python -m verifieds.<x> commands found in README"

    for mod_name in set(matches):
        full_name = f"verifieds.{mod_name}"
        spec = importlib.util.find_spec(full_name)
        assert spec is not None, (
            f"Module {full_name} named in README could not be found"
        )


def test_report_outline_contents() -> None:
    """Validate docs/REPORT_OUTLINE.md exists and contains sections."""
    outline_path = Path(__file__).parent.parent / "docs" / "REPORT_OUTLINE.md"
    assert outline_path.exists()

    content = outline_path.read_text(encoding="utf-8")
    assert "Architecture & Design" in content
    assert "Evaluation & Results" in content
