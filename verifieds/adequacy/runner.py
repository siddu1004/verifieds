"""Runner module for workload adequacy mutation testing (node Q4 / D-7)."""

import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from verifieds.adequacy.mutator import OperatorSwap, apply_mutation, find_mutation_sites
from verifieds.harness.runner import compare
from verifieds.schemas.models import AdequacyReport, MutantResult

ROOT = Path(__file__).resolve().parent.parent.parent


def find_gpp() -> str:
    """Locate g++ executable on PATH or WinLibs location."""
    found = shutil.which("g++")
    if found:
        return found
    if sys.platform == "win32":
        winget_pkg = Path(
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        )
        for cand in winget_pkg.glob("*WinLibs*/mingw64/bin"):
            gpp_exe = cand / "g++.exe"
            if gpp_exe.exists():
                return str(gpp_exe)
    raise RuntimeError("g++ compiler not found. Please ensure MinGW/g++ is installed.")


def run_single_mutant(
    idx: int,
    site: OperatorSwap,
    source_dir: Path,
    tmp_base: Path,
    orig_cli_path: Path,
    gpp_path: str,
    seed: int,
) -> MutantResult:
    """Compile and evaluate equivalence for a single mutant site."""
    mutant_dir = tmp_base / f"mutant_{idx}"
    src_dir = mutant_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Copy all source files from source_dir into src_dir
    for src_file in source_dir.glob("*.[hc]pp"):
        shutil.copy2(src_file, src_dir / src_file.name)

    # Apply mutation to target file
    target_file = src_dir / site.file
    if target_file.exists():
        content = target_file.read_text(encoding="utf-8")
        mutated_content = apply_mutation(content, site)
        target_file.write_text(mutated_content, encoding="utf-8")

    # Compile mutant binary
    exe_name = f"sim_cli_{idx}.exe" if sys.platform == "win32" else f"sim_cli_{idx}"
    mutant_exe = mutant_dir / exe_name

    main_cpp = source_dir / "main.cpp"
    cmd = [
        gpp_path,
        "-std=c++20",
        "-O2",
        "-I",
        str(src_dir),
        str(main_cpp),
        "-o",
        str(mutant_exe),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15.0)
        if proc.returncode != 0:
            return MutantResult(
                file=site.file,
                line=site.line,
                status="invalid",
                **{"from": site.from_op, "to": site.to_op},
            )
    except Exception:
        return MutantResult(
            file=site.file,
            line=site.line,
            status="invalid",
            **{"from": site.from_op, "to": site.to_op},
        )

    # Evaluate equivalence across policies and quantum settings
    policies = [
        ("FCFS", None),
        ("SJF", None),
        ("SRTF", None),
        ("RR", 1),
        ("RR", 3),
        ("PRIORITY", None),
    ]

    is_killed = False
    for p_idx, (policy, quantum) in enumerate(policies):
        try:
            res = compare(
                original=[str(orig_cli_path)],
                candidate=[str(mutant_exe)],
                sizes=[10, 30],
                policy=policy,
                quantum=quantum,
                seed=seed + idx * 10 + p_idx,
            )
            if not res.equivalent:
                is_killed = True
                break
        except Exception:
            is_killed = True
            break

    status_str: Literal["killed", "survived", "invalid"] = (
        "killed" if is_killed else "survived"
    )
    return MutantResult(
        file=site.file,
        line=site.line,
        status=status_str,
        **{"from": site.from_op, "to": site.to_op},
    )


def run_adequacy_assessment(
    source_dir: Path | None = None,
    files: list[str] | None = None,
    seed: int = 1,
    max_mutants: int = 60,
    max_workers: int = 4,
) -> AdequacyReport:
    """Run workload adequacy assessment over mutation sites in C++ source files."""
    if source_dir is None:
        source_dir = ROOT / "sim" / "src"
    if files is None:
        files = ["Scheduler.hpp", "ReadyQueue.hpp"]

    gpp_path = find_gpp()
    orig_cli = (
        ROOT / "build" / ("sim_cli.exe" if sys.platform == "win32" else "sim_cli")
    )

    if not orig_cli.exists():
        # Build original sim_cli first
        subprocess.run([sys.executable, "tasks.py", "build-sim"], cwd=ROOT, check=True)

    # Collect mutation sites ordered by file, line, column
    sites: list[OperatorSwap] = []
    for fname in files:
        fpath = source_dir / fname
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8")
            sites.extend(find_mutation_sites(fname, content))

    capped_sites = sites[:max_mutants]

    tmp_base = ROOT / "build" / "tmp_adequacy"
    if tmp_base.exists():
        shutil.rmtree(tmp_base, ignore_errors=True)
    tmp_base.mkdir(parents=True, exist_ok=True)

    results: list[MutantResult] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_single_mutant,
                idx,
                site,
                source_dir,
                tmp_base,
                orig_cli,
                gpp_path,
                seed,
            )
            for idx, site in enumerate(capped_sites)
        ]
        for f in futures:
            results.append(f.result())

    killed = sum(1 for r in results if r.status == "killed")
    survived = sum(1 for r in results if r.status == "survived")
    invalid = sum(1 for r in results if r.status == "invalid")

    denom = killed + survived
    score = (killed / denom) if denom > 0 else 1.0

    return AdequacyReport(
        mutants=results,
        killed=killed,
        survived=survived,
        invalid=invalid,
        score=round(score, 4),
    )
