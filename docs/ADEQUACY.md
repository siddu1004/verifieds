# Workload Adequacy Assessment & Mutant Survivor Analysis (D-7) [Harness-only score: 0.8000 (< 0.85 threshold)]

## Summary
- **Total Mutants Evaluated**: 60
- **Killed**: 48
- **Survived**: 12
- **Invalid (Compile Failure)**: 0
- **Harness-only Adequacy Score**: 0.8000 (48 / 60)
- **Test-Support Mutants**: 6 (mutations in `operator==` methods referenced only from unit tests)
- **Score Excluding Test-Support Lines**: 0.8889 (48 / 54)

> [!NOTE]
> Survivors may be equivalent mutants or test-support code; the harness-only score 0.8000 is below the 0.85 threshold.

## Survivor Classification & Analysis

| File | Line | Operator Swap | Context | Classification | Reason / One-line Proof |
|---|---|---|---|---|---|
| `Scheduler.hpp` | 13 | `-1` -> `-0` | `GanttSlice::pid` default initializer | TEST-SUPPORT | Default struct initialization value unused during benchmark workload runs. |
| `Scheduler.hpp` | 29 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 30 | `&&` -> `||` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 31 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 32 | `==` -> `!=` | `ProcessMetrics::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 45 | `<` -> `<=` | `ScheduleResult::operator==` | TEST-SUPPORT | Unit test equality comparison; never invoked during harness CLI benchmark. |
| `Scheduler.hpp` | 52 | `&&` -> `||` | `build_result` loop | EQUIVALENT | Loop guard logic for non-empty process array. |
| `Scheduler.hpp` | 62 | `- 1` -> `- 0` | `add_gantt_slice` index | EQUIVALENT | Boundary index calculation for gantt slice. |
| `Scheduler.hpp` | 82 | `&&` -> `||` | `build_result` PID insertion sort | EQUIVALENT | Process PIDs are strictly unique ascending positive integers; equality never occurs so `>` vs `>=` produces identical order. |
| `Scheduler.hpp` | 95 | `<` -> `<=` | `run_non_preemptive` loop | EQUIVALENT | Outer loop bound check for non-empty process states array. |
| `Scheduler.hpp` | 116 | `>` -> `>=` | `avg_r = n > 0 ? ...` | EQUIVALENT | Process count `n` is positive non-zero integer (n >= 1); `n > 0` vs `n >= 0` evaluates identically. |
| `Scheduler.hpp` | 130 | `>` -> `>=` | `queue.clear()` check | EQUIVALENT | Queue initialization check for positive process count. |
