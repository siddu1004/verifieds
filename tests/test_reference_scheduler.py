"""Tests for reference_scheduler.py validating golden schedules (Q0)."""

from tests.reference_scheduler import schedule

SET_A = [
    (1, 0, 8, 3),
    (2, 1, 4, 1),
    (3, 2, 9, 4),
    (4, 3, 5, 2),
]

SET_B = [
    (1, 0, 5, 2),
    (2, 2, 3, 1),
    (3, 4, 1, 3),
]


def test_set_a_constant() -> None:
    assert SET_A == [
        (1, 0, 8, 3),
        (2, 1, 4, 1),
        (3, 2, 9, 4),
        (4, 3, 5, 2),
    ]


def test_reference_scheduler_set_a_fcfs() -> None:
    gantt, metrics = schedule(SET_A, "FCFS")
    assert gantt == [(1, 0, 8), (2, 8, 12), (3, 12, 21), (4, 21, 26)]
    assert metrics[1] == (8, 8, 0, 0)
    assert metrics[2] == (12, 11, 7, 7)
    assert metrics[3] == (21, 19, 10, 10)
    assert metrics[4] == (26, 23, 18, 18)


def test_reference_scheduler_set_a_sjf() -> None:
    gantt, metrics = schedule(SET_A, "SJF")
    assert gantt == [(1, 0, 8), (2, 8, 12), (4, 12, 17), (3, 17, 26)]
    assert metrics[1] == (8, 8, 0, 0)
    assert metrics[2] == (12, 11, 7, 7)
    assert metrics[3] == (26, 24, 15, 15)
    assert metrics[4] == (17, 14, 9, 9)


def test_reference_scheduler_set_a_srtf() -> None:
    gantt, metrics = schedule(SET_A, "SRTF")
    assert gantt == [(1, 0, 1), (2, 1, 5), (4, 5, 10), (1, 10, 17), (3, 17, 26)]
    assert metrics[1] == (17, 17, 9, 0)
    assert metrics[2] == (5, 4, 0, 0)
    assert metrics[3] == (26, 24, 15, 15)
    assert metrics[4] == (10, 7, 2, 2)


def test_reference_scheduler_set_a_rr() -> None:
    gantt, metrics = schedule(SET_A, "RR", quantum=3)
    assert gantt == [
        (1, 0, 3),
        (2, 3, 6),
        (3, 6, 9),
        (4, 9, 12),
        (1, 12, 15),
        (2, 15, 16),
        (3, 16, 19),
        (4, 19, 21),
        (1, 21, 23),
        (3, 23, 26),
    ]
    assert metrics[1] == (23, 23, 15, 0)


def test_reference_scheduler_set_a_priority() -> None:
    gantt, metrics = schedule(SET_A, "PRIORITY")
    assert gantt == [(1, 0, 8), (2, 8, 12), (4, 12, 17), (3, 17, 26)]
    assert metrics[2] == (12, 11, 7, 7)
