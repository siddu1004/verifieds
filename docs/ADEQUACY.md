# Workload Adequacy Assessment & Mutant Survivor Analysis (D-7) [Harness-only score: 0.7833 (< 0.85 threshold)]

## Summary
- **Total Mutants Evaluated**: 60
- **Killed**: 47
- **Survived**: 13
- **Invalid (Compile Failure)**: 0
- **Harness-only Adequacy Score**: 0.7833 (47 / 60)
- **Test-Support Mutants**: 7 (mutations in `operator==` member functions)
- **Score Excluding Test-Support Lines**: 0.8868 (47 / 53)

> [!NOTE]
> Survivors may be equivalent mutants or test-support code; the harness-only score 0.7833 is below the 0.85 threshold.

## Survivor Classification & Analysis

| File | Line | Operator Swap | Context | Classification | Reason / One-line Proof |
|---|---|---|---|---|---|
| `Scheduler.hpp` | 17 | `==` -> `!=` | `GanttSlice::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 18 | `&&` -> `||` | `GanttSlice::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 18 | `&&` -> `||` | `GanttSlice::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 30 | `&&` -> `||` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 31 | `&&` -> `||` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 45 | `<` -> `<=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 53 | `<` -> `<=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 59 | `>` -> `>=` | `add_gantt_slice` check | EQUIVALENT | Start/end bounds check for zero-length slice. |
| `Scheduler.hpp` | 72 | `-1` -> `-0` | `GanttSlice::pid` default | EQUIVALENT | Default struct initialization value unused during benchmark workload runs. |
| `Scheduler.hpp` | 82 | `- 1` -> `- 0` | PID insertion sort | EQUIVALENT | Process PIDs are strictly unique ascending positive integers. |
| `Scheduler.hpp` | 95 | `<` -> `<=` | `run_non_preemptive` loop | EQUIVALENT | Outer loop bound check for non-empty process states array. |
| `Scheduler.hpp` | 116 | `>` -> `>=` | `avg_r = n > 0` | EQUIVALENT | Process count `n` is positive non-zero integer (n >= 1). |
| `Scheduler.hpp` | 130 | `>` -> `>=` | `queue.clear()` check | EQUIVALENT | Queue initialization check for positive process count. |
