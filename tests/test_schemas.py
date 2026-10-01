"""Tests for Pydantic schemas and schema export verification (S-04)."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from verifieds.schemas.models import Finding, Candidate, VerifyReport, WorkloadResult
from verifieds.schemas.export import export_schemas, check_schemas


def test_finding_valid_and_roundtrip() -> None:
    """Finding model valid instantiations and JSON roundtrip."""
    finding = Finding(
        id="hash123",
        rule_id="array-queue-front-removal",
        file="sim/src/queue.cpp",
        start_line=10,
        end_line=15,
        adt="queue",
        impl="ArrayQueue",
        complexity_before="O(n)",
        evidence="pop_front shifts all elements",
    )
    dumped = finding.model_dump_json()
    loaded = Finding.model_validate_json(dumped)
    assert loaded == finding


def test_finding_invalid_adt_rejected() -> None:
    """Finding must reject invalid ADT value."""
    with pytest.raises(ValidationError):
        Finding(
            id="hash123",
            rule_id="array-queue-front-removal",
            file="sim/src/queue.cpp",
            start_line=10,
            end_line=15,
            adt="invalid_adt",  # type: ignore[arg-type]
            impl="ArrayQueue",
            complexity_before="O(n)",
            evidence="evidence",
        )


def test_candidate_valid_and_roundtrip() -> None:
    """Candidate model valid instantiation and JSON roundtrip."""
    cand = Candidate(
        id="cand_1",
        finding_id="hash123",
        strategy="replace with circular queue",
        diff="--- a/sim/src/queue.cpp\n+++ b/sim/src/queue.cpp\n",
        expected_complexity_after="O(1)",
        risks=["memory overhead"],
    )
    dumped = cand.model_dump_json()
    loaded = Candidate.model_validate_json(dumped)
    assert loaded == cand


def test_verify_report_valid_and_roundtrip() -> None:
    """VerifyReport model valid instantiation and JSON roundtrip."""
    report = VerifyReport(
        candidate_id="cand_1",
        equivalent=True,
        rejected_reason=None,
        workloads=[
            WorkloadResult(
                n=100,
                original_ms_median=1.2,
                candidate_ms_median=0.4,
                runs=7,
            )
        ],
        speedup_at_max_n=3.0,
        crossover_n=100,
    )
    dumped = report.model_dump_json()
    loaded = VerifyReport.model_validate_json(dumped)
    assert loaded == report


def test_schema_export_and_check(tmp_path: Path) -> None:
    """Exporting schemas and checking staleness."""
    schemas_dir = tmp_path / "schemas"
    export_schemas(schemas_dir)

    assert (schemas_dir / "finding.json").exists()
    assert (schemas_dir / "candidate.json").exists()
    assert (schemas_dir / "verify_report.json").exists()

    # Check passes when up-to-date
    assert check_schemas(schemas_dir) is True

    # Check fails when missing a file
    (schemas_dir / "finding.json").unlink()
    assert check_schemas(schemas_dir) is False

    # Corrupt one schema file to simulate staleness
    (schemas_dir / "finding.json").write_text(json.dumps({"stale": True}))
    assert check_schemas(schemas_dir) is False


def test_export_main_check_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with --check when schemas are up-to-date."""
    from verifieds.schemas import export

    monkeypatch.setattr(export, "check_schemas", lambda _path: True)
    monkeypatch.setattr("sys.argv", ["export", "--check"])
    export.main()


def test_export_main_check_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with --check when schemas are stale."""
    from verifieds.schemas import export

    monkeypatch.setattr(export, "check_schemas", lambda _path: False)
    monkeypatch.setattr("sys.argv", ["export", "--check"])
    with pytest.raises(SystemExit) as exc_info:
        export.main()
    assert exc_info.value.code == 1


def test_export_main_export(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() without --check (export mode)."""
    from verifieds.schemas import export

    exported = False

    def dummy_export(_path: Path) -> None:
        nonlocal exported
        exported = True

    monkeypatch.setattr(export, "export_schemas", dummy_export)
    monkeypatch.setattr("sys.argv", ["export"])
    export.main()
    assert exported is True
