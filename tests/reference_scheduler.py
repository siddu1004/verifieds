"""Independent reference scheduler for tests. Pure Python, shares no code with C++."""

from collections import deque

IDLE = -1


def _emit(gantt, pid, start, end):
    if end <= start:
        return
    if gantt and gantt[-1][0] == pid and gantt[-1][2] == start:
        gantt[-1] = (pid, gantt[-1][1], end)
    else:
        gantt.append((pid, start, end))


def _metrics(procs, first_start, completion):
    result = {}
    for pid, arrival, burst, _priority in procs:
        turnaround = completion[pid] - arrival
        result[pid] = (
            completion[pid],
            turnaround,
            turnaround - burst,
            first_start[pid] - arrival,
        )
    return result


def _next_arrival(procs, remaining):
    return min(arr for pid, arr, _b, _p in procs if remaining[pid] > 0)


def _non_preemptive(procs, policy):
    keys = {
        "FCFS": lambda p: (p[1], p[0]),
        "SJF": lambda p: (p[2], p[1], p[0]),
        "PRIORITY": lambda p: (p[3], p[1], p[0]),
    }
    remaining = {p[0]: p[2] for p in procs}
    first_start, completion, gantt = {}, {}, []
    now = 0
    while any(remaining.values()):
        ready = [p for p in procs if remaining[p[0]] > 0 and p[1] <= now]
        if not ready:
            nxt = _next_arrival(procs, remaining)
            _emit(gantt, IDLE, now, nxt)
            now = nxt
            continue
        pid, _arr, burst, _prio = min(ready, key=keys[policy])
        first_start[pid] = now
        _emit(gantt, pid, now, now + burst)
        now += burst
        completion[pid] = now
        remaining[pid] = 0
    return gantt, _metrics(procs, first_start, completion)


def _srtf(procs):
    remaining = {p[0]: p[2] for p in procs}
    arrival = {p[0]: p[1] for p in procs}
    first_start, completion, gantt = {}, {}, []
    now, current = 0, None
    while any(remaining.values()):
        ready = [pid for pid in remaining if remaining[pid] > 0 and arrival[pid] <= now]
        if not ready:
            nxt = _next_arrival(procs, remaining)
            _emit(gantt, IDLE, now, nxt)
            now, current = nxt, None
            continue
        best = min(ready, key=lambda k: (remaining[k], arrival[k], k))
        if current in ready and remaining[current] <= remaining[best]:
            best = current
        current = best
        first_start.setdefault(current, now)
        _emit(gantt, current, now, now + 1)
        remaining[current] -= 1
        now += 1
        if remaining[current] == 0:
            completion[current] = now
            current = None
    return gantt, _metrics(procs, first_start, completion)


def _round_robin(procs, quantum):
    remaining = {p[0]: p[2] for p in procs}
    arrival = {p[0]: p[1] for p in procs}
    order = sorted(remaining, key=lambda k: (arrival[k], k))
    queue, queued = deque(), set()
    first_start, completion, gantt = {}, {}, []
    now = 0

    def admit(upto):
        for pid in order:
            if pid not in queued and arrival[pid] <= upto:
                queue.append(pid)
                queued.add(pid)

    admit(now)
    while any(remaining.values()):
        if not queue:
            nxt = min(arrival[k] for k in order if k not in queued)
            _emit(gantt, IDLE, now, nxt)
            now = nxt
            admit(now)
            continue
        pid = queue.popleft()
        first_start.setdefault(pid, now)
        step = min(quantum, remaining[pid])
        _emit(gantt, pid, now, now + step)
        now += step
        remaining[pid] -= step
        admit(now)
        if remaining[pid] == 0:
            completion[pid] = now
        else:
            queue.append(pid)
    return gantt, _metrics(procs, first_start, completion)


def schedule(procs, policy, quantum=None):
    """procs: (pid, arrival, burst, priority). Returns (gantt, {pid: (completion,
    turnaround, waiting, response)}); idle slices use pid -1."""
    if policy == "SRTF":
        return _srtf(procs)
    if policy == "RR":
        return _round_robin(procs, quantum)
    return _non_preemptive(procs, policy)
