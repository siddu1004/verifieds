"""Tests for verifieds.harness."""

import sys
from pathlib import Path
import pytest
from verifieds.harness.runner import (
    BenchmarkRunner,
    compare,
    generate_workload,
    set_memory_limit,
)

ROOT = Path(__file__).resolve().parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


@pytest.fixture(scope="session")
def sim_cli_path() -> Path:
    cli_path = ROOT / "build" / exe_name("sim_cli")
    assert cli_path.exists(), "sim_cli executable must exist"
    return cli_path


def test_generate_workload():
    wl1 = generate_workload(10, seed=42)
    wl2 = generate_workload(10, seed=42)
    wl3 = generate_workload(10, seed=43)
    assert len(wl1) == 10
    assert wl1 == wl2
    assert wl1 != wl3


def test_set_memory_limit_windows():
    if sys.platform == "win32":
        with pytest.raises(NotImplementedError, match="D-4"):
            set_memory_limit(1024 * 1024)


def test_harness_with_sim_cli(sim_cli_path: Path):
    res = compare(
        [str(sim_cli_path)],
        [str(sim_cli_path)],
        sizes=[50, 100],
        seed=1,
    )
    assert res["equivalent"] is True
    assert res["speedup_at_max_n"] is not None
    assert abs(res["speedup_at_max_n"] - 1.0) < 0.5


def test_harness_synthetic_on_vs_on2(tmp_path: Path):
    script_on = tmp_path / "on.py"
    script_on2 = tmp_path / "on2.py"

    # Synthetic O(n) script
    script_on.write_text(
        "import sys, time\n"
        "with open(sys.argv[2]) as f: text = f.read()\n"
        "procs = len(text.splitlines()) - 3\n"
        "time.sleep(procs * 0.001)\n"
        'print(\'{"policy": "FCFS", "gantt": [], "metrics": {}}\')\n',
        encoding="utf-8",
    )

    # Synthetic O(n^2) script (same output, slower)
    script_on2.write_text(
        "import sys, time\n"
        "with open(sys.argv[2]) as f: text = f.read()\n"
        "procs = len(text.splitlines()) - 3\n"
        "time.sleep((procs ** 2) * 0.0001)\n"
        'print(\'{"policy": "FCFS", "gantt": [], "metrics": {}}\')\n',
        encoding="utf-8",
    )

    py = [sys.executable]
    runner = BenchmarkRunner(
        py + [str(script_on2)], py + [str(script_on)], runs_per_size=3
    )
    res = runner.run_benchmark(sizes=[10, 50], seed=10, tmp_dir=tmp_path / "tmp")

    assert res["equivalent"] is True
    assert res["speedup_at_max_n"] > 1.0
    assert res["crossover_n"] is not None


def test_harness_non_equivalent(tmp_path: Path):
    script1 = tmp_path / "s1.py"
    script2 = tmp_path / "s2.py"

    script1.write_text("print('{\"a\": 1}')\n", encoding="utf-8")
    script2.write_text("print('{\"a\": 2}')\n", encoding="utf-8")

    py = [sys.executable]
    runner = BenchmarkRunner(py + [str(script1)], py + [str(script2)])
    res = runner.run_benchmark(sizes=[10], seed=1, tmp_dir=tmp_path / "tmp")

    assert res["equivalent"] is False
    assert res["reason"] is not None


def test_harness_runaway_timeout(tmp_path: Path):
    script_inf = tmp_path / "inf.py"
    script_inf.write_text("import time\nwhile True: time.sleep(1)\n", encoding="utf-8")

    py = [sys.executable]
    runner = BenchmarkRunner(
        py + [str(script_inf)], py + [str(script_inf)], timeout_sec=0.5
    )
    res = runner.run_benchmark(sizes=[5], seed=1, tmp_dir=tmp_path / "tmp")

    assert res["equivalent"] is False
    assert "exit code" in res["reason"].lower() or "timeout" in res["reason"].lower()
