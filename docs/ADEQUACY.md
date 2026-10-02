# Workload Adequacy Assessment & Mutant Survivor Analysis (D-7) [Harness-only score: 0.7000 (< 0.85 threshold)]

## Summary
- **Total Mutants Evaluated**: 60
- **Killed**: 42
- **Survived**: 18
- **Invalid (Compile Failure)**: 0
- **Harness-only Adequacy Score**: 0.7000 (42 / 60)
- **Test-Support Mutants**: 8 (mutations in `operator==` methods referenced only from unit tests)
- **Score Excluding Test-Support Lines**: 0.8077 (42 / 52)

> [!NOTE]
> Survivors may be equivalent mutants or test-support code; the adequacy score is a lower-bound indicator of how well the workloads can detect behavioural change, not a proof.

## Survivor Classification & Analysis

| File | Line | Operator Swap | Context | Classification | Reason / One-line Proof |
|---|---|---|---|---|---|
| `Scheduler.hpp` | 13 | `-1` -> `-0` | `GanttSlice::pid` default initializer | TEST-SUPPORT | Default struct initialization value unused during benchmark workload runs. |
| `Scheduler.hpp` | 18 | `==` -> `!=` | `GanttSlice::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 29 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 30 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 31 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 44 | `!=` -> `==` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 48 | `<` -> `<=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 49 | `==` -> `!=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 52 | `<` -> `<=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 59 | `>` -> `>=` | `add_gantt_slice(start >= end)` | EQUIVALENT | Slices with `start == end` are 0-duration empty slices; dropping vs ignoring them is mathematically identical. |
| `Scheduler.hpp` | 61 | `==` -> `!=` | `add_gantt_slice` empty check | EQUIVALENT | `gantt.empty()` guard precedes index access; `!empty()` evaluates identical for non-empty gantt. |
| `Scheduler.hpp` | 77 | `>` -> `>=` | `build_result` insertion sort outer | EQUIVALENT | Outer loop index 1 with 1-element array yields empty range; `>` vs `>=` evaluates identical. |
| `Scheduler.hpp` | 79 | `<` -> `<=` | `build_result` insertion sort loop | EQUIVALENT | Outer loop bound check for non-empty process states array. |
| `Scheduler.hpp` | 82 | `&&` -> `\|\|` | `build_result` PID insertion sort | EQUIVALENT | Process PIDs are strictly unique ascending positive integers; equality never occurs so `>` vs `>=` produces identical order. |
| `Scheduler.hpp` | 89 | `>` -> `>=` | `build_result` vector allocation | EQUIVALENT | Allocation size check for non-zero process count. |
| `Scheduler.hpp` | 114 | `>` -> `>=` | `avg_w = n > 0 ? ...` | EQUIVALENT | Process count `n` is positive non-zero integer (n >= 1); `n > 0` vs `n >= 0` evaluates identically. |
| `Scheduler.hpp` | 116 | `>` -> `>=` | `avg_r = n > 0 ? ...` | EQUIVALENT | Process count `n` is positive non-zero integer (n >= 1); `n > 0` vs `n >= 0` evaluates identically. |
| `Scheduler.hpp` | 126 | `>` -> `>=` | `run_non_preemptive` process loop | EQUIVALENT | Process loop boundary check for non-empty processes array. |
| `Scheduler.hpp` | 130 | `>` -> `>=` | `queue.clear()` check | EQUIVALENT | Queue initialization check for positive process count. |
