"""Study script test suite (S-11)."""

from pathlib import Path
from unittest.mock import patch

from verifieds.study.runner import main, run_study


def test_study_dry_run_deterministic(tmp_path: Path) -> None:
    """Dry-run study sweep produces identical CSV files on consecutive runs."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    raw1, sum1 = run_study(dir1, dry_run=True)
    raw2, sum2 = run_study(dir2, dry_run=True)

    assert raw1.exists() and sum1.exists()
    assert raw2.exists() and sum2.exists()

    assert raw1.read_bytes() == raw2.read_bytes()
    assert sum1.read_bytes() == sum2.read_bytes()


def test_study_main_cli(tmp_path: Path) -> None:
    """CLI main entry point executes cleanly."""
    out_dir = tmp_path / "cli_out"
    test_args = ["run_study.py", "--out-dir", str(out_dir), "--dry-run"]
    with patch("sys.argv", test_args):
        main()
    assert (out_dir / "study_results.csv").exists()
    assert (out_dir / "summary_stats.csv").exists()


def test_study_real_proposer_fallback(tmp_path: Path) -> None:
    """Non-dry-run study handles proposer fallback gracefully."""
    out_dir = tmp_path / "fallback"
    raw_p, sum_p = run_study(
        out_dir, dry_run=False, models=["test_model"], policies=["FCFS"]
    )
    assert raw_p.exists() and sum_p.exists()
