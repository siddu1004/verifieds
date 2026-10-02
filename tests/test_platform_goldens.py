"""Platform golden tests for C++ simulator output (T5).

Validates that JSON golden files in tests/golden/platform match:
1. Hand-computed expectation values (HAND table from test_scenarios_sim.py).
2. Direct sim_cli execution outputs on Windows and Linux CI.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from reference_scheduler import IDLE

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden" / "platform"

# MinGW environment setup for Windows test execution
if sys.platform == "win32" and not shutil.which("g++"):
    winget_pkg = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
    for candidate in winget_pkg.glob("*WinLibs*/mingw64/bin"):
        if (candidate / "g++.exe").exists():
            os.environ["PATH"] = (
                str(candidate) + os.path.pathsep + os.environ.get("PATH", "")
            )
            break

CONVOY = [(1, 0, 20, 3), (2, 1, 1, 1), (3, 2, 1, 1), (4, 3, 1, 2)]
TIES = [(i, 0, 4, 2) for i in range(1, 6)]
PRIORITY_WAIT = [(1, 0, 5, 9), (2, 1, 2, 1), (3, 2, 2, 1), (4, 3, 2, 1)]
SET_A = [(1, 0, 10, 3), (2, 1, 4, 1), (3, 2, 2, 4), (4, 3, 1, 2)]
SET_B = [(1, 0, 5, 2), (2, 2, 3, 1), (3, 4, 1, 3)]

SCENARIO_PROCS: dict[str, tuple[list[tuple[int, int, int, int]], int | None]] = {
    "sc1_convoy": (CONVOY, 2),
    "sc2_ties": (TIES, 2),
    "sc3_priority_wait": (PRIORITY_WAIT, 2),
    "set_a": (SET_A, 3),
    "set_b": (SET_B, 3),
}

HAND_EXPECTATIONS = {
    "sc1_convoy_fcfs": ("P1[0-20] P2[20-21] P3[21-22] P4[22-23]", (14.25, 20.0, 14.25)),
    "sc1_convoy_sjf": ("P1[0-20] P2[20-21] P3[21-22] P4[22-23]", (14.25, 20.0, 14.25)),
    "sc1_convoy_priority": (
        "P1[0-20] P2[20-21] P3[21-22] P4[22-23]",
        (14.25, 20.0, 14.25),
    ),
    "sc1_convoy_srtf": ("P1[0-1] P2[1-2] P3[2-3] P4[3-4] P1[4-23]", (0.75, 6.5, 0.0)),
    "sc1_convoy_rr": (
        "P1[0-2] P2[2-3] P3[3-4] P1[4-6] P4[6-7] P1[7-23]",
        (2.0, 7.75, 1.25),
    ),
    "sc2_ties_fcfs": ("P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]", (8.0, 12.0, 8.0)),
    "sc2_ties_sjf": ("P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]", (8.0, 12.0, 8.0)),
    "sc2_ties_srtf": ("P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]", (8.0, 12.0, 8.0)),
    "sc2_ties_priority": (
        "P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]",
        (8.0, 12.0, 8.0),
    ),
    "sc2_ties_rr": (
        "P1[0-2] P2[2-4] P3[4-6] P4[6-8] P5[8-10] P1[10-12] P2[12-14] P3[14-16]"
        " P4[16-18] P5[18-20]",
        (12.0, 16.0, 4.0),
    ),
    "sc3_priority_wait_priority": (
        "P1[0-5] P2[5-7] P3[7-9] P4[9-11]",
        (3.75, 6.5, 3.75),
    ),
}


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


@pytest.fixture(scope="module")
def cli() -> Path:
    path = ROOT / "build" / exe_name("sim_cli")
    if not path.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "tasks.py"), "build-sim"], check=True, cwd=ROOT
        )
    return path


def gantt_text(gantt_list: list[dict[str, int]]) -> str:
    parts = []
    for slice_item in gantt_list:
        pid, start, end = slice_item["pid"], slice_item["start"], slice_item["end"]
        label = "IDLE" if pid == IDLE else f"P{pid}"
        parts.append(f"{label}[{start}-{end}]")
    return " ".join(parts)


def test_goldens_exist_and_match_hand_table() -> None:
    """Verify all 45 golden files exist and match HAND table expectations."""
    assert GOLDEN_DIR.exists(), f"Golden dir {GOLDEN_DIR} does not exist"
    golden_files = list(GOLDEN_DIR.glob("*.json"))
    assert len(golden_files) == 45, (
        f"Expected 45 golden files, found {len(golden_files)}"
    )

    for hand_key, (expected_text, expected_avgs) in HAND_EXPECTATIONS.items():
        matching_goldens = [
            f
            for f in golden_files
            if f.name.startswith(f"{hand_key}_") or f.name == f"{hand_key}.json"
        ]
        assert len(matching_goldens) > 0, (
            f"No golden file found for hand expectation {hand_key}"
        )
        for g_file in matching_goldens:
            content = json.loads(g_file.read_text(encoding="utf-8"))
            text = gantt_text(content["gantt"])
            assert text == expected_text, (
                f"Gantt mismatch in {g_file.name}: got {text!r},"
                f" expected {expected_text!r}"
            )
            assert content["avg_waiting"] == pytest.approx(expected_avgs[0], abs=0.005)
            assert content["avg_turnaround"] == pytest.approx(
                expected_avgs[1], abs=0.005
            )
            assert content["avg_response"] == pytest.approx(expected_avgs[2], abs=0.005)


def test_sim_cli_matches_platform_goldens(cli: Path) -> None:
    """Verify sim_cli execution output matches every JSON golden file exactly."""
    golden_files = sorted(GOLDEN_DIR.glob("*.json"))
    assert len(golden_files) == 45

    for g_file in golden_files:
        golden_data = json.loads(g_file.read_text(encoding="utf-8"))
        stem = g_file.stem
        # parse scenario name from stem, e.g. sc1_convoy_fcfs_array
        sc_name = None
        for name in SCENARIO_PROCS:
            if stem.startswith(name):
                sc_name = name
                break
        assert sc_name is not None, f"Could not determine scenario for {g_file.name}"

        procs, default_q = SCENARIO_PROCS[sc_name]
        policy = golden_data["policy"]
        backend = golden_data["backend"]
        quantum = default_q if policy == "RR" else None

        lines = [f"policy={policy}", f"backend={backend}"]
        if quantum is not None:
            lines.append(f"quantum={quantum}")
        lines.append(f"processes={len(procs)}")
        lines += [" ".join(map(str, p)) for p in procs]

        with tempfile.TemporaryDirectory() as tmp:
            batch_path = Path(tmp) / "batch.txt"
            batch_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [str(cli), "--batch", str(batch_path)],
                capture_output=True,
                text=True,
                check=True,
            )

        cli_output_data = json.loads(proc.stdout)
        assert cli_output_data == golden_data, (
            f"sim_cli output mismatch for golden {g_file.name}"
        )
