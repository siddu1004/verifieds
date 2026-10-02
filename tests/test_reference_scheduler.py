"""Tests for reference_scheduler.py validating golden schedules (Q0)."""

from tests.reference_scheduler import schedule

SET_A = [
    (1, 0, 10, 3),
    (2, 1, 4, 1),
    (3, 2, 2, 4),
    (4, 3, 1, 2),
]

SET_B = [
    (1, 0, 5, 2),
    (2, 2, 3, 1),
    (3, 4, 1, 3),
]


def test_reference_scheduler_set_a_fcfs() -> None:
    gantt, metrics = schedule(SET_A, "FCFS")
    assert gantt == [(1, 0, 10), (2, 10, 14), (3, 14, 16), (4, 16, 17)]
    assert metrics[1] == (10, 10, 0, 0)
    assert metrics[2] == (14, 13, 9, 9)
    assert metrics[3] == (16, 14, 12, 12)
    assert metrics[4] == (17, 14, 13, 13)


def test_reference_scheduler_set_a_sjf() -> None:
    gantt, metrics = schedule(SET_A, "SJF")
    assert gantt == [(1, 0, 10), (4, 10, 11), (3, 11, 13), (2, 13, 17)]
    assert metrics[1] == (10, 10, 0, 0)
    assert metrics[4] == (11, 8, 7, 7)
    assert metrics[3] == (13, 11, 9, 9)
    assert metrics[2] == (17, 16, 12, 12)


def test_reference_scheduler_set_a_srtf() -> None:
    gantt, metrics = schedule(SET_A, "SRTF")
    assert gantt == [(1, 0, 1), (2, 1, 2), (3, 2, 4), (4, 4, 5), (2, 5, 8), (1, 8, 17)]
    assert metrics[3] == (4, 2, 0, 0)
    assert metrics[4] == (5, 2, 1, 1)


def test_reference_scheduler_set_a_rr() -> None:
    gantt, metrics = schedule(SET_A, "RR", quantum=3)
    assert gantt == [
        (1, 0, 3),
        (2, 3, 6),
        (3, 6, 8),
        (4, 8, 9),
        (1, 9, 12),
        (2, 12, 13),
        (1, 13, 17),
    ]


def test_reference_scheduler_set_a_priority() -> None:
    gantt, metrics = schedule(SET_A, "PRIORITY")
    assert gantt == [(1, 0, 10), (2, 10, 14), (4, 14, 15), (3, 15, 17)]
    assert metrics[2] == (14, 13, 9, 9)
    assert metrics[4] == (15, 12, 11, 11)


def test_reference_scheduler_set_b() -> None:
    gantt_fcfs, _ = schedule(SET_B, "FCFS")
    assert gantt_fcfs == [(1, 0, 5), (2, 5, 8), (3, 8, 9)]

    gantt_prio, _ = schedule(SET_B, "PRIORITY")
    assert gantt_prio == [(1, 0, 5), (2, 5, 8), (3, 8, 9)]
