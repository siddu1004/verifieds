"""Benchmark runner and equivalence verification harness."""

import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from verifieds.schemas.models import VerifyReport, WorkloadResult

ROOT = Path(__file__).resolve().parent.parent.parent

if sys.platform == "win32" and not shutil.which("g++"):
    winget_pkg = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
    for _cand in winget_pkg.glob("*WinLibs*/mingw64/bin"):
        if (_cand / "g++.exe").exists():
            os.environ["PATH"] = (
                str(_cand) + os.path.pathsep + os.environ.get("PATH", "")
            )
            break


def set_memory_limit(limit_bytes: int) -> None:
    """Set memory limit for harness subprocesses.

    On Windows, resource.setrlimit is unavailable, so raise NotImplementedError
    per DECISION D-4.
    """
    if sys.platform == "win32":
        raise NotImplementedError("Memory limits are not supported on Windows (D-4)")
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))


def compile_program(source_dir: Path, main_file: str, out_path: Path) -> Path:
    """Compile C++ program using g++ -std=c++20 -O2 -I<source_dir>."""
    gpp = shutil.which("g++")
    if not gpp and sys.platform == "win32":
        winget_pkg = Path(
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        )
        for cand in winget_pkg.glob("*WinLibs*/mingw64/bin"):
            if (cand / "g++.exe").exists():
                gpp = str(cand / "g++.exe")
                break
    if not gpp:
        raise RuntimeError("g++ compiler not found.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    main_path = (
        source_dir / main_file if not Path(main_file).is_absolute() else Path(main_file)
    )

    cmd = [
        gpp,
        "-std=c++20",
        "-O2",
        f"-I{source_dir}",
        str(main_path),
        "-o",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        msg = (
            f"Compiler error (exit code {proc.returncode}):\n"
            f"{proc.stderr}\n{proc.stdout}"
        )
        raise RuntimeError(msg)
    return out_path


def generate_workload(
    n: int,
    seed: int = 42,
    path: Path | None = None,
    policy: str = "SJF",
    quantum: int | None = None,
    ties: bool = False,
) -> list[tuple[int, int, int, int]]:
    """Generate workload of n processes: (pid, arrival, burst, priority)."""
    rng = random.Random(seed)
    procs: list[tuple[int, int, int, int]] = []
    current_arr = 0
    for pid in range(1, n + 1):
        if rng.random() < 0.7:
            current_arr += rng.randint(0, 2)
        else:
            current_arr += rng.randint(3, 8)

        if ties:
            burst = rng.choice([1, 2, 3])
            priority = rng.choice([1, 2])
        elif policy in ("SJF", "SRTF"):
            burst = rng.choice([1, 2, 3, 4, 5, 8])
            priority = rng.randint(1, 10)
        elif policy == "PRIORITY":
            burst = rng.randint(1, 15)
            priority = rng.choice([1, 2, 3, 4])
        else:
            burst = rng.randint(1, 20)
            priority = rng.randint(1, 10)

        procs.append((pid, current_arr, burst, priority))

    if path is not None:
        write_batch_file(path, procs, policy=policy, quantum=quantum)

    return procs


def write_batch_file(
    path: Path,
    procs: list[tuple[int, int, int, int]],
    policy: str = "SJF",
    backend: str | None = None,
    quantum: int | None = None,
) -> None:
    """Write process batch file for sim_cli."""
    lines = [f"policy={policy}"]
    if backend is not None:
        lines.append(f"backend={backend}")
    if quantum is not None:
        lines.append(f"quantum={quantum}")
    lines.append(f"processes={len(procs)}")
    for pid, arr, burst, prio in procs:
        lines.append(f"{pid} {arr} {burst} {prio}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


class BenchmarkRunner:
    """Compiles, runs, measures and compares execution of binaries."""

    def __init__(
        self,
        orig_cmd: list[str],
        cand_cmd: list[str],
        candidate_id: str = "c1",
        runs_per_size: int = 7,
        timeout_sec: float = 10.0,
    ) -> None:
        self.orig_cmd = orig_cmd
        self.cand_cmd = cand_cmd
        self.candidate_id = candidate_id
        self.runs_per_size = runs_per_size
        self.timeout_sec = timeout_sec

    def _run_single(
        self, cmd: list[str], input_text: str | None = None
    ) -> tuple[int, str, float]:
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
            )
            dt = time.perf_counter() - t0
            return proc.returncode, proc.stdout, dt
        except subprocess.TimeoutExpired:
            return -1, "", self.timeout_sec

    def run_benchmark(
        self,
        sizes: list[int] | None = None,
        policy: str = "SJF",
        quantum: int | None = None,
        seed: int = 42,
        tmp_dir: Path | None = None,
    ) -> VerifyReport:
        """Run benchmark over workload sizes and compute crossover_n and speedup."""
        if sizes is None:
            sizes = [100, 1000, 10000]

        if tmp_dir is None:
            tmp_dir = ROOT / "build" / "tmp_harness"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        orig_times: dict[int, list[float]] = {}
        cand_times: dict[int, list[float]] = {}
        equivalent = True
        mismatch_reason: str | None = None
        workload_results: list[WorkloadResult] = []

        for n in sizes:
            workload = generate_workload(
                n, seed=seed + n, policy=policy, quantum=quantum
            )
            batch_file = tmp_dir / f"workload_{n}.txt"
            write_batch_file(batch_file, workload, policy=policy, quantum=quantum)

            # Check output equivalence on run 1
            code_o, out_o, _ = self._run_single(
                self.orig_cmd + ["--batch", str(batch_file)]
            )
            code_c, out_c, _ = self._run_single(
                self.cand_cmd + ["--batch", str(batch_file)]
            )

            if code_o != 0 or code_c != 0:
                equivalent = False
                mismatch_reason = f"Non-zero exit code: orig={code_o}, cand={code_c}"
                break

            hash_o = hashlib.sha256(out_o.encode("utf-8")).hexdigest()
            hash_c = hashlib.sha256(out_c.encode("utf-8")).hexdigest()

            if hash_o != hash_c:
                try:
                    data_o = json.loads(out_o)
                    data_c = json.loads(out_c)
                    if isinstance(data_o, dict) and isinstance(data_c, dict):
                        data_o = dict(data_o)
                        data_c = dict(data_c)
                        data_o.pop("backend", None)
                        data_c.pop("backend", None)
                    if data_o != data_c:
                        equivalent = False
                        mismatch_reason = f"Output mismatch at n={n}"
                        break
                except json.JSONDecodeError:
                    equivalent = False
                    mismatch_reason = f"JSON decode error or mismatch at n={n}"
                    break

            # Measure timing across runs
            o_runtimes: list[float] = []
            c_runtimes: list[float] = []
            for _ in range(self.runs_per_size):
                _, _, dt_o = self._run_single(
                    self.orig_cmd + ["--batch", str(batch_file)]
                )
                _, _, dt_c = self._run_single(
                    self.cand_cmd + ["--batch", str(batch_file)]
                )
                o_runtimes.append(dt_o)
                c_runtimes.append(dt_c)

            orig_times[n] = o_runtimes
            cand_times[n] = c_runtimes

            med_o = statistics.median(o_runtimes) * 1000.0
            med_c = statistics.median(c_runtimes) * 1000.0
            workload_results.append(
                WorkloadResult(
                    n=n,
                    original_ms_median=round(med_o, 3),
                    candidate_ms_median=round(med_c, 3),
                    runs=self.runs_per_size,
                )
            )

        if not equivalent:
            return VerifyReport(
                candidate_id=self.candidate_id,
                equivalent=False,
                rejected_reason=mismatch_reason or "Output mismatch",
                workloads=[],
            )

        # Calculate medians and crossover
        medians_orig = {n: statistics.median(orig_times[n]) for n in sizes}
        medians_cand = {n: statistics.median(cand_times[n]) for n in sizes}

        max_n = max(sizes)
        speedup = (
            medians_orig[max_n] / medians_cand[max_n]
            if medians_cand[max_n] > 0
            else 1.0
        )

        # Crossover n logic: smallest n where cand range does not overlap orig range
        crossover_n: int | None = None
        for n in sorted(sizes):
            min_o = min(orig_times[n])
            max_c = max(cand_times[n])
            if max_c < min_o:
                crossover_n = n
                break

        return VerifyReport(
            candidate_id=self.candidate_id,
            equivalent=True,
            rejected_reason=None,
            workloads=workload_results,
            speedup_at_max_n=round(max(speedup, 0.001), 4),
            crossover_n=crossover_n,
        )


def compare(
    original: Path | list[str] | str,
    candidate: Path | list[str] | str,
    candidate_id: str = "c1",
    sizes: list[int] | None = None,
    runs: int = 7,
    seed: int = 1234,
    *,
    timer: Any = time.perf_counter,
    policy: str = "SJF",
    quantum: int | None = None,
) -> VerifyReport:
    """Top-level compare function (CompareFn signature)."""
    _ = timer
    orig_cmd = (
        [str(original)]
        if isinstance(original, (str, Path))
        else [str(x) for x in original]
    )
    cand_cmd = (
        [str(candidate)]
        if isinstance(candidate, (str, Path))
        else [str(x) for x in candidate]
    )

    runner = BenchmarkRunner(
        orig_cmd, cand_cmd, candidate_id=candidate_id, runs_per_size=runs
    )
    return runner.run_benchmark(sizes=sizes, policy=policy, quantum=quantum, seed=seed)
