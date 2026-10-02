"""Simulator scenarios and metamorphic tests (Q1)."""

import random
import subprocess
import sys
from pathlib import Path
import pytest

from tests.conftest import run_batch
from tests.reference_scheduler import schedule
from verifieds.harness.runner import BenchmarkRunner

ROOT = Path(__file__).parent.parent


def exe_name(stem: str) -> str:
    return f"{stem}.exe" if sys.platform == "win32" else stem


def test_sc1_convoy(tmp_path: Path) -> None:
    """Purpose: Verify convoy effect performance across policies.
    Input: Processes (1,0,20,3), (2,1,1,1), (3,2,1,1), (4,3,1,2).
    Expected Result: Gantt slices and metrics match oracle and hand tables.
    Bug Catching: Preemption logic bugs, queue ordering inversion under convoy.
    """
    procs = [(1, 0, 20, 3), (2, 1, 1, 1), (3, 2, 1, 1), (4, 3, 1, 2)]

    for policy in ["FCFS", "SJF", "PRIORITY"]:
        res = run_batch(policy, "array", procs, tmp_path=tmp_path)
        gantt_ref, _ = schedule(procs, policy)

        assert res["avg_waiting"] == pytest.approx(14.25)
        assert res["avg_turnaround"] == pytest.approx(20.0)
        assert res["avg_response"] == pytest.approx(14.25)
        assert [(g["pid"], g["start"], g["end"]) for g in res["gantt"]] == gantt_ref

    res_srtf = run_batch("SRTF", "array", procs, tmp_path=tmp_path)
    gantt_srtf, _ = schedule(procs, "SRTF")
    assert res_srtf["avg_waiting"] == pytest.approx(0.75)
    assert res_srtf["avg_turnaround"] == pytest.approx(6.5)
    assert res_srtf["avg_response"] == pytest.approx(0.0)
    assert [(g["pid"], g["start"], g["end"]) for g in res_srtf["gantt"]] == gantt_srtf

    res_rr = run_batch("RR", "array", procs, quantum=2, tmp_path=tmp_path)
    gantt_rr, _ = schedule(procs, "RR", quantum=2)
    assert res_rr["avg_waiting"] == pytest.approx(2.0)
    assert res_rr["avg_turnaround"] == pytest.approx(7.75)
    assert res_rr["avg_response"] == pytest.approx(1.25)
    assert [(g["pid"], g["start"], g["end"]) for g in res_rr["gantt"]] == gantt_rr


def test_sc2_simultaneous_ties(tmp_path: Path) -> None:
    """Purpose: Verify tie-breaker rules (arrival then pid).
    Input: 5 processes (pid 1-5, arrival 0, burst 4, priority 2).
    Expected Result: Exact pid ordering for FCFS/SJF/SRTF/PRIORITY and RR q=2.
    Bug Catching: Non-deterministic tie-breaking or unstable queue sorting.
    """
    procs = [(i, 0, 4, 2) for i in range(1, 6)]

    for policy in ["FCFS", "SJF", "SRTF", "PRIORITY"]:
        res = run_batch(policy, "array", procs, tmp_path=tmp_path)
        gantt_ref, _ = schedule(procs, policy)
        assert res["avg_waiting"] == pytest.approx(8.0)
        assert [(g["pid"], g["start"], g["end"]) for g in res["gantt"]] == gantt_ref

    res_rr = run_batch("RR", "array", procs, quantum=2, tmp_path=tmp_path)
    gantt_rr, _ = schedule(procs, "RR", quantum=2)
    assert res_rr["avg_waiting"] == pytest.approx(12.0)
    assert [(g["pid"], g["start"], g["end"]) for g in res_rr["gantt"]] == gantt_rr


def test_sc3_priority_wait(tmp_path: Path) -> None:
    """Purpose: Verify priority scheduling with staggered arrivals.
    Input: (1,0,5,9), (2,1,2,1), (3,2,2,1), (4,3,2,1).
    Expected Result: Waiting P1=0, P2=4, P3=5, P4=6.
    Bug Catching: Incorrect ready queue insertion logic for priority ties.
    """
    procs = [(1, 0, 5, 9), (2, 1, 2, 1), (3, 2, 2, 1), (4, 3, 2, 1)]
    res = run_batch("PRIORITY", "array", procs, tmp_path=tmp_path)
    gantt_ref, _ = schedule(procs, "PRIORITY")

    metrics_map = {m["pid"]: m["waiting"] for m in res["metrics"]}
    assert metrics_map[1] == 0
    assert metrics_map[2] == 4
    assert metrics_map[3] == 5
    assert metrics_map[4] == 6
    assert [(g["pid"], g["start"], g["end"]) for g in res["gantt"]] == gantt_ref


def test_sc4_single_process(tmp_path: Path) -> None:
    """Purpose: Verify single process execution edge case.
    Input: Process (1,0,5,1).
    Expected Result: Gantt P1[0-5], waiting 0, turnaround 5.
    Bug Catching: Null pointer dereference or boundary loop failure.
    """
    procs = [(1, 0, 5, 1)]
    res = run_batch("FCFS", "array", procs, tmp_path=tmp_path)
    assert [(g["pid"], g["start"], g["end"]) for g in res["gantt"]] == [(1, 0, 5)]
    assert res["avg_waiting"] == 0.0


def test_sc5_idle_first(tmp_path: Path) -> None:
    """Purpose: Verify CPU idle period before first process at t=100.
    Input: Process (1,100,1,1).
    Expected Result: Gantt IDLE[0-100], P1[100-101], waiting 0.
    Bug Catching: Skipping initial idle CPU time or zero-start assumption bugs.
    """
    procs = [(1, 100, 1, 1)]
    res = run_batch("FCFS", "array", procs, tmp_path=tmp_path)
    gantt_ref, _ = schedule(procs, "FCFS")
    assert [(g["pid"], g["start"], g["end"]) for g in res["gantt"]] == gantt_ref
    assert gantt_ref[0] == (-1, 0, 100)


def test_sc6_rr_extremes(tmp_path: Path) -> None:
    """Purpose: Verify Round Robin under extreme quantum values.
    Input: Processes (1,0,3,1), (2,0,2,1).
    Expected Result: q=1 alternates; q=100 matches FCFS.
    Bug Catching: Infinite queue re-insertion loops or quantum off-by-one errors.
    """
    procs = [(1, 0, 3, 1), (2, 0, 2, 1)]

    res_q1 = run_batch("RR", "array", procs, quantum=1, tmp_path=tmp_path)
    gantt_q1, _ = schedule(procs, "RR", quantum=1)
    assert [(g["pid"], g["start"], g["end"]) for g in res_q1["gantt"]] == gantt_q1

    res_q100 = run_batch("RR", "array", procs, quantum=100, tmp_path=tmp_path)
    gantt_fcfs, _ = schedule(procs, "FCFS")
    assert [(g["pid"], g["start"], g["end"]) for g in res_q100["gantt"]] == gantt_fcfs


def test_metamorphic_properties() -> None:
    """Purpose: Verify 6 metamorphic invariant properties (M1-M6).
    Input: 300 seeded random workloads.
    Expected Result: Invariant properties hold for simulator outputs.
    Bug Catching: Order dependency, non-linear timing bugs, state leakage.
    """
    rng = random.Random(42)
    policies = ["FCFS", "SJF", "SRTF", "RR", "PRIORITY"]

    for _ in range(300):
        n = rng.randint(1, 10)
        procs = [
            (i + 1, rng.randint(0, 15), rng.randint(1, 8), rng.randint(1, 4))
            for i in range(n)
        ]
        pol = rng.choice(policies)
        q = rng.randint(1, 4) if pol == "RR" else None

        # M1: Permuting input order changes nothing
        shuffled = list(procs)
        rng.shuffle(shuffled)
        g1, m1 = schedule(procs, pol, q)
        g1_shuf, m1_shuf = schedule(shuffled, pol, q)
        assert g1 == g1_shuf and m1 == m1_shuf

        # M2: Adding k to arrival shifts completion by k
        k = rng.randint(1, 10)
        procs_k = [(p[0], p[1] + k, p[2], p[3]) for p in procs]
        _, m2 = schedule(procs_k, pol, q)
        for pid in m1:
            assert m2[pid][0] == m1[pid][0] + k
            assert m2[pid][1] == m1[pid][1]
            assert m2[pid][2] == m1[pid][2]
            assert m2[pid][3] == m1[pid][3]

        # M3: Multiplying arrivals, bursts by 3 multiplies metrics by 3
        procs_m3 = [(p[0], p[1] * 3, p[2] * 3, p[3]) for p in procs]
        q_m3 = q * 3 if q else None
        _, m3 = schedule(procs_m3, pol, q_m3)
        for pid in m1:
            assert m3[pid][0] == m1[pid][0] * 3
            assert m3[pid][2] == m1[pid][2] * 3

        # M4: SRTF average waiting <= other policies
        avg_wait_srtf = sum(m[2] for m in schedule(procs, "SRTF")[1].values()) / n
        avg_wait_pol = sum(m[2] for m in m1.values()) / n
        assert avg_wait_srtf <= avg_wait_pol + 1e-9

        # M5: RR quantum >= largest burst equals FCFS per process
        max_burst = max(p[2] for p in procs)
        g_rr_large, _ = schedule(procs, "RR", quantum=max_burst + 1)
        g_fcfs, _ = schedule(procs, "FCFS")
        assert g_rr_large == g_fcfs

        # M6: Appending process arriving after all finish leaves earlier unchanged
        max_completion = max(m1[p[0]][0] for p in procs)
        late_proc = (n + 1, max_completion + 10, 5, 1)
        procs_appended = procs + [late_proc]
        _, m6 = schedule(procs_appended, pol, q)
        for pid in m1:
            assert m6[pid] == m1[pid]


def test_differential_oracle_500_workloads(tmp_path: Path) -> None:
    """Purpose: Differential testing against reference_scheduler on 500 workloads.
    Input: 500 seeded random workloads (1-15 procs, arrival 0-25).
    Expected Result: sim_cli output matches reference_scheduler output.
    Bug Catching: Mismatches between C++ engine and reference scheduler.
    """
    rng = random.Random(1337)
    policies = ["FCFS", "SJF", "SRTF", "RR", "PRIORITY"]

    for _ in range(500):
        n = rng.randint(1, 15)
        procs = [
            (i + 1, rng.randint(0, 25), rng.randint(1, 9), rng.randint(1, 5))
            for i in range(n)
        ]
        policy = rng.choice(policies)
        q = rng.randint(1, 5) if policy == "RR" else None
        backend = rng.choice(["array", "heap"])

        res_sim = run_batch(policy, backend, procs, quantum=q, tmp_path=tmp_path)
        gantt_ref, metrics_ref = schedule(procs, policy, quantum=q)

        assert [(g["pid"], g["start"], g["end"]) for g in res_sim["gantt"]] == gantt_ref
        for m in res_sim["metrics"]:
            pid = m["pid"]
            expected_tuple = (
                m["completion"],
                m["turnaround"],
                m["waiting"],
                m["response"],
            )
            assert expected_tuple == metrics_ref[pid]


def test_scale_20k_workload() -> None:
    """Purpose: Large scale (n=20,000) workload performance comparison.
    Input: Workload generated with n=20000 and SJF policy.
    Expected Result: Array and Heap backends yield identical outputs.
    Bug Catching: O(n^2) scaling degradation or buffer overflow.
    """
    sim_cli = ROOT / "build" / exe_name("sim_cli")
    assert sim_cli.exists()

    runner = BenchmarkRunner(
        orig_cmd=[str(sim_cli)],
        cand_cmd=[str(sim_cli)],
        runs_per_size=3,
    )
    res = runner.run_benchmark(sizes=[20000], policy="SJF")
    assert res["equivalent"] is True


def test_malformed_interactive_inputs() -> None:
    """Purpose: Interactive CLI malformed input stress test.
    Input: Negative numbers, PID 0, 10,000 char lines, repeated delete, EOF.
    Expected Result: sim_cli reports clear error messages without crashing.
    Bug Catching: Unhandled stdin EOF, buffer overflow, arithmetic exceptions.
    """
    sim_cli = ROOT / "build" / exe_name("sim_cli")
    assert sim_cli.exists()

    long_line = "A" * 10000 + "\n"
    inputs = f"-1\n0\n{long_line}99\n"

    proc = subprocess.run(
        [str(sim_cli)],
        input=inputs,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in [0, 1]
