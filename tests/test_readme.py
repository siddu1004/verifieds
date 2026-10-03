"""README validation tests (S-12)."""

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


def test_report_outline_contents() -> None:
    """Validate docs/REPORT_OUTLINE.md exists and contains sections."""
    outline_path = Path(__file__).parent.parent / "docs" / "REPORT_OUTLINE.md"
    assert outline_path.exists()

    content = outline_path.read_text(encoding="utf-8")
    assert "Architecture & Design" in content
    assert "Evaluation & Results" in content
