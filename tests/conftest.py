"""conftest.py – shared pytest fixtures and test helpers."""

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from verifieds.harness.runner import write_batch_file

ROOT = Path(__file__).parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


def run_batch(
    policy: str,
    backend: str,
    procs: list[tuple[int, int, int, int]],
    quantum: int | None = None,
    tmp_path: Path | None = None,
) -> dict[str, Any]:
    """Write batch file, run sim_cli executable, and return parsed JSON result."""
    work_dir = tmp_path or (ROOT / "build")
    work_dir.mkdir(parents=True, exist_ok=True)
    batch_file = work_dir / "batch_input.txt"

    write_batch_file(batch_file, procs, policy=policy, backend=backend, quantum=quantum)

    sim_cli = ROOT / "build" / exe_name("sim_cli")
    assert sim_cli.exists(), f"sim_cli executable not found at {sim_cli}"

    res = subprocess.run(
        [str(sim_cli), "--batch", str(batch_file)],
        capture_output=True,
        text=True,
        check=True,
    )

    stdout_clean = res.stdout.replace("\r\n", "\n")
    return json.loads(stdout_clean)  # type: ignore[no-any-return]
