import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


@pytest.fixture(scope="session", autouse=True)
def ensure_sim_cli():
    cli_path = ROOT / "build" / exe_name("sim_cli")
    if not cli_path.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "tasks.py"), "build-sim"], check=True, cwd=ROOT
        )
    return cli_path


def test_batch_mode_set_a_all_policies(tmp_path: Path, ensure_sim_cli: Path):
    policies = ["FCFS", "SJF", "SRTF", "PRIORITY"]
    backends = ["array", "heap"]

    for pol in policies:
        for backend in backends:
            batch_file = tmp_path / f"batch_{pol}_{backend}.txt"
            batch_file.write_text(
                f"policy={pol}\n"
                f"backend={backend}\n"
                "processes=4\n"
                "1 0 8 3\n"
                "2 1 4 1\n"
                "3 2 9 4\n"
                "4 3 5 2\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [str(ensure_sim_cli), "--batch", str(batch_file)],
                capture_output=True,
                text=True,
                check=True,
            )

            data = json.loads(proc.stdout)
            assert data["policy"] == pol
            assert data["backend"] == backend
            assert len(data["gantt"]) > 0
            assert len(data["metrics"]) == 4


def test_batch_mode_rr(tmp_path: Path, ensure_sim_cli: Path):
    batch_file = tmp_path / "batch_rr.txt"
    batch_file.write_text(
        "policy=RR\nquantum=3\nprocesses=4\n1 0 8 3\n2 1 4 1\n3 2 9 4\n4 3 5 2\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(ensure_sim_cli), "--batch", str(batch_file)],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(proc.stdout)
    assert data["policy"] == "RR"
    assert abs(data["avg_waiting"] - 13.5) < 0.005
    assert abs(data["avg_turnaround"] - 20.0) < 0.005
    assert abs(data["avg_response"] - 3.0) < 0.005


def test_interactive_mode(ensure_sim_cli: Path):
    # Test script: add process, display, exit
    commands = "1\n1 0 5 1\n5\n9\n"
    proc = subprocess.run(
        [str(ensure_sim_cli)],
        input=commands,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "VerifiedDS Simulator CLI" in proc.stdout
    assert "PID=1" in proc.stdout
    assert "Exiting CLI." in proc.stdout


def test_batch_mode_malformed(tmp_path: Path, ensure_sim_cli: Path):
    batch_file = tmp_path / "bad.txt"
    batch_file.write_text("invalid line format\n", encoding="utf-8")

    proc = subprocess.run(
        [str(ensure_sim_cli), "--batch", str(batch_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert (
        "error" in proc.stderr.lower()
        or "malformed" in proc.stderr.lower()
        or len(proc.stderr) > 0
    )
