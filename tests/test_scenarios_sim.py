"""Scenario and property tests for sim_cli, judged by an independent oracle.

Expected values come from hand-computed tables below and from
reference_scheduler.py (pure Python, shares no code with the C++ program).
Never derive an expected value from sim_cli's own output.
"""

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from reference_scheduler import IDLE, schedule

ROOT = Path(__file__).resolve().parent.parent
POLICIES = ("FCFS", "SJF", "SRTF", "PRIORITY", "RR")


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


def run_cli(cli, policy, procs, quantum=None, backend="heap"):
    lines = [f"policy={policy}", f"backend={backend}"]
    if quantum is not None:
        lines.append(f"quantum={quantum}")
    lines.append(f"processes={len(procs)}")
    lines += [" ".join(map(str, p)) for p in procs]
    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp) / "batch.txt"
        batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
        proc = subprocess.run(
            [str(cli), "--batch", str(batch)],
            capture_output=True,
            text=True,
            check=True,
        )
    return json.loads(proc.stdout)


def gantt_of(out):
    return [(s["pid"], s["start"], s["end"]) for s in out["gantt"]]


def metrics_of(out):
    return {
        m["pid"]: (m["completion"], m["turnaround"], m["waiting"], m["response"])
        for m in out["metrics"]
    }


def gantt_text(out):
    parts = []
    for pid, start, end in gantt_of(out):
        label = "IDLE" if pid == IDLE else f"P{pid}"
        parts.append(f"{label}[{start}-{end}]")
    return " ".join(parts)


def assert_oracle(cli, procs, policy, quantum=None, backend="heap"):
    out = run_cli(cli, policy, procs, quantum, backend)
    gantt, metrics = schedule(procs, policy, quantum)
    assert gantt_of(out) == gantt
    assert metrics_of(out) == metrics
    return out


CONVOY = [(1, 0, 20, 3), (2, 1, 1, 1), (3, 2, 1, 1), (4, 3, 1, 2)]
TIES = [(i, 0, 4, 2) for i in range(1, 6)]
PRIORITY_WAIT = [(1, 0, 5, 9), (2, 1, 2, 1), (3, 2, 2, 1), (4, 3, 2, 1)]

HAND = [
    (
        "convoy-fcfs",
        CONVOY,
        "FCFS",
        None,
        "P1[0-20] P2[20-21] P3[21-22] P4[22-23]",
        (14.25, 20.0, 14.25),
    ),
    (
        "convoy-sjf",
        CONVOY,
        "SJF",
        None,
        "P1[0-20] P2[20-21] P3[21-22] P4[22-23]",
        (14.25, 20.0, 14.25),
    ),
    (
        "convoy-priority",
        CONVOY,
        "PRIORITY",
        None,
        "P1[0-20] P2[20-21] P3[21-22] P4[22-23]",
        (14.25, 20.0, 14.25),
    ),
    (
        "convoy-srtf",
        CONVOY,
        "SRTF",
        None,
        "P1[0-1] P2[1-2] P3[2-3] P4[3-4] P1[4-23]",
        (0.75, 6.5, 0.0),
    ),
    (
        "convoy-rr2",
        CONVOY,
        "RR",
        2,
        "P1[0-2] P2[2-3] P3[3-4] P1[4-6] P4[6-7] P1[7-23]",
        (2.0, 7.75, 1.25),
    ),
    (
        "ties-fcfs",
        TIES,
        "FCFS",
        None,
        "P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]",
        (8.0, 12.0, 8.0),
    ),
    (
        "ties-sjf",
        TIES,
        "SJF",
        None,
        "P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]",
        (8.0, 12.0, 8.0),
    ),
    (
        "ties-srtf",
        TIES,
        "SRTF",
        None,
        "P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]",
        (8.0, 12.0, 8.0),
    ),
    (
        "ties-priority",
        TIES,
        "PRIORITY",
        None,
        "P1[0-4] P2[4-8] P3[8-12] P4[12-16] P5[16-20]",
        (8.0, 12.0, 8.0),
    ),
    (
        "ties-rr2",
        TIES,
        "RR",
        2,
        "P1[0-2] P2[2-4] P3[4-6] P4[6-8] P5[8-10] P1[10-12] P2[12-14] P3[14-16]"
        " P4[16-18] P5[18-20]",
        (12.0, 16.0, 4.0),
    ),
    (
        "priority-wait",
        PRIORITY_WAIT,
        "PRIORITY",
        None,
        "P1[0-5] P2[5-7] P3[7-9] P4[9-11]",
        (3.75, 6.5, 3.75),
    ),
]


@pytest.mark.parametrize(
    ("procs", "policy", "quantum", "text", "avgs"),
    [pytest.param(*h[1:], id=h[0]) for h in HAND],
)
def test_hand_computed_scenarios(cli, procs, policy, quantum, text, avgs):
    """Claim: Core simulator structures (DynArray, BST, MinHeap, ReadyQueue)
    and multi-policy study results (FCFS, SJF, SRTF, RR, PRIORITY).

    Input: tables above. Expected: exact Gantt text and averages from hand
    computation, also equal to the oracle. Catches: wrong tie-breaks, wrong
    preemption rule, wrong RR queue order.
    """

    for backend in ("array", "heap") if policy != "RR" else ("array",):
        out = assert_oracle(cli, procs, policy, quantum, backend)
        assert gantt_text(out) == text
        assert out["avg_waiting"] == pytest.approx(avgs[0], abs=0.005)
        assert out["avg_turnaround"] == pytest.approx(avgs[1], abs=0.005)
        assert out["avg_response"] == pytest.approx(avgs[2], abs=0.005)


@pytest.mark.parametrize("policy", POLICIES)
def test_single_and_late_process(cli, policy):
    """Purpose: degenerate inputs. Input: one process at 0; one process at 100.
    Expected: no idle for the first; IDLE[0-100] then the process for the second.
    Catches: crashes on tiny input, missing leading idle slice."""
    quantum = 3 if policy == "RR" else None
    out = assert_oracle(cli, [(1, 0, 5, 1)], policy, quantum)
    assert gantt_text(out) == "P1[0-5]"
    out = assert_oracle(cli, [(1, 100, 1, 1)], policy, quantum)
    assert gantt_text(out) == "IDLE[0-100] P1[100-101]"


@pytest.mark.parametrize("quantum", [1, 1000])
def test_round_robin_extremes(cli, quantum):
    """Purpose: RR with quantum 1 and a huge quantum. Expected: equals the
    oracle; the huge quantum behaves like FCFS. Catches: quantum off-by-one."""
    assert_oracle(cli, CONVOY, "RR", quantum)


def random_procs(rng, max_n, max_arrival, max_burst):
    n = rng.randint(1, max_n)
    return [
        (
            i + 1,
            rng.randint(0, max_arrival),
            rng.randint(1, max_burst),
            rng.randint(1, 5),
        )
        for i in range(n)
    ]


def test_differential_against_oracle(cli):
    """Purpose: broad agreement with the independent oracle. Input: 100 seeded
    workloads, all policies, both queue backends. Expected: identical Gantt and
    metrics. Catches: any scheduling logic bug the named scenarios miss."""
    rng = random.Random(2026)
    for _ in range(100):
        procs = random_procs(rng, 15, 25, 9)
        for policy in POLICIES:
            quantum = rng.randint(1, 6) if policy == "RR" else None
            for backend in ("array", "heap") if policy != "RR" else ("array",):
                assert_oracle(cli, procs, policy, quantum, backend)


def test_metamorphic_properties(cli):
    """Purpose: properties that must hold for every workload (40 seeded).
    M1 input order is irrelevant. M2 shifting all arrivals by k keeps waiting,
    turnaround, response and moves completion by k. M3 scaling times (and the
    quantum) by 3 scales completion and waiting by 3. M4 SRTF has the lowest
    average waiting. M5 RR with quantum >= max burst equals FCFS. M6 a process
    arriving after everything finished changes no earlier result.
    Catches: order dependence, hidden absolute-time assumptions, preemption bugs."""
    rng = random.Random(7)
    for _ in range(40):
        procs = random_procs(rng, 10, 15, 8)
        quantum = rng.randint(1, 4)
        base = {}
        for policy in POLICIES:
            q = quantum if policy == "RR" else None
            base[policy] = metrics_of(run_cli(cli, policy, procs, q))
            shuffled = procs[:]
            rng.shuffle(shuffled)
            assert metrics_of(run_cli(cli, policy, shuffled, q)) == base[policy]  # M1
            k = rng.randint(1, 9)
            shifted = [(a, b + k, c, d) for a, b, c, d in procs]
            moved = metrics_of(run_cli(cli, policy, shifted, q))  # M2
            for pid, (comp, turn, wait, resp) in base[policy].items():
                assert moved[pid] == (comp + k, turn, wait, resp)
            scaled = [(a, b * 3, c * 3, d) for a, b, c, d in procs]
            sq = None if q is None else q * 3
            big = metrics_of(run_cli(cli, policy, scaled, sq))  # M3
            for pid, (comp, _turn, wait, _resp) in base[policy].items():
                assert big[pid][0] == comp * 3
                assert big[pid][2] == wait * 3
            end = max(m[0] for m in base[policy].values())
            tail = [*procs, (len(procs) + 1, end + 50, 3, 1)]
            after = metrics_of(run_cli(cli, policy, tail, q))  # M6
            for pid, values in base[policy].items():
                assert after[pid] == values
        avg = {p: sum(m[2] for m in base[p].values()) / len(procs) for p in POLICIES}
        assert all(avg["SRTF"] <= avg[p] + 1e-9 for p in POLICIES)  # M4
        longest = max(p[2] for p in procs)
        assert metrics_of(run_cli(cli, "RR", procs, longest)) == base["FCFS"]  # M5


def test_scale_backends_agree(cli):
    """Purpose: a larger workload (3,000 processes). Expected: both queue backends
    produce identical output. Catches: heap bugs that only appear with deep heaps."""
    rng = random.Random(5)
    procs = [
        (i + 1, rng.randint(0, 750), rng.randint(1, 20), rng.randint(1, 10))
        for i in range(3000)
    ]
    for policy in ("SJF", "PRIORITY", "FCFS"):
        first = run_cli(cli, policy, procs, backend="array")
        second = run_cli(cli, policy, procs, backend="heap")
        first.pop("backend")
        second.pop("backend")
        assert first == second
