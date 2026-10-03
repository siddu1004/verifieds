"""Unit tests for verifieds.smoke (R-09)."""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

from verifieds.schemas.models import CandidateDraft
from verifieds.smoke import main

ROOT = Path(__file__).resolve().parent.parent


def test_smoke_invalid_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["smoke.py", "--file", "../outside.cpp"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_smoke_no_findings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clean_file = tmp_path / "clean.cpp"
    clean_file.write_text("int main() { return 0; }\n", encoding="utf-8")
    monkeypatch.setenv("VERIFIEDS_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["smoke.py", "--file", str(clean_file)])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_smoke_with_finding_and_fake_proposer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "main.cpp"
    target.write_text(
        """#include <iostream>
int main() {
    int arr[10] = {0};
    for (int i = 0; i < 9; ++i) {
        arr[i] = arr[i + 1];
    }
    return 0;
}
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("VERIFIEDS_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["smoke.py", "--file", str(target)])

    dummy_draft = CandidateDraft(
        strategy="Test strategy",
        diff="--- a/main.cpp\n+++ b/main.cpp\n",
        expected_complexity_after="O(1)",
        risks=[],
    )

    with (
        patch("verifieds.smoke.OllamaProposer") as mock_proposer_cls,
        patch("verifieds.smoke.build_verify_diff") as mock_verify_builder,
    ):
        instance = mock_proposer_cls.return_value
        instance.propose.return_value = [dummy_draft]

        mock_verify_fn = mock_verify_builder.return_value
        mock_report = mock_verify_fn.return_value
        mock_report.equivalent = True
        mock_report.speedup_at_max_n = 2.5

        main()
