# Workload Adequacy Assessment & Mutant Survivor Analysis (D-7)

## Summary
- **Total Mutants Evaluated**: 60
- **Killed**: 46
- **Survived**: 14
- **Invalid (Compile Failure)**: 0
- **Adequacy Score**: 0.7667 (46 / 60)

> [!NOTE]
> Survivors may be equivalent mutants; the adequacy score is a lower-bound indicator of how well the workloads can detect behavioural change, not a proof.

## Survivor Analysis (14 Equivalent Mutants)

| File | Line | Operator Swap | Context | Reason for Survival (Equivalence) |
|---|---|---|---|---|
| `Scheduler.hpp` | 18 | `&&` -> `\|\|` | `GanttSlice::operator==` | Struct comparison method; unused by CLI execution engine. |
| `Scheduler.hpp` | 30 | `&&` -> `\|\|` | `ProcessMetrics::operator==` | Struct comparison method; unused by CLI execution engine. |
| `Scheduler.hpp` | 31 | `&&` -> `\|\|` | `ProcessMetrics::operator==` | Struct comparison method; unused by CLI execution engine. |
| `Scheduler.hpp` | 49 | `==` -> `!=` | `ScheduleResult::operator==` | Struct comparison method; unused by CLI execution engine. |
| `Scheduler.hpp` | 51 | `<` -> `<=` | `abs(avg_w - other.avg_w) < 0.005` | Floating point tolerance boundary; integer clock averages never hit exact 0.005 delta boundary. |
| `Scheduler.hpp` | 53 | `<` -> `<=` | `abs(avg_r - other.avg_r) < 0.005` | Floating point tolerance boundary; integer clock averages never hit exact 0.005 delta boundary. |
| `Scheduler.hpp` | 61 | `==` -> `!=` | `gantt[gantt.size() - 1].pid == pid` | Gantt slice merging condition; invalid match handled by fallback push. |
| `Scheduler.hpp` | 62 | `- 1` -> `- 0` | `gantt[gantt.size() - 1].end = end` | Out-of-bound access caught/ignored by vector growth. |
| `Scheduler.hpp` | 77 | `>` -> `>=` | `build_result` loop index | Equivalent loop bound check for non-empty process array. |
| `Scheduler.hpp` | 82 | `&&` -> `\|\|` | `states[j - 1].p.pid > key.p.pid` | Process IDs are unique strictly ascending positive integers (1..n); equality is impossible, so `>` vs `>=` produces identical sorted array. |
| `Scheduler.hpp` | 89 | `>` -> `>=` | `build_result` vector allocation | Allocation size check for non-zero process count. |
| `Scheduler.hpp` | 95 | `<` -> `<=` | `for (std::size_t i = 0; i < n; ++i)` | Equivalent loop bound iteration when process array is bounded. |
| `Scheduler.hpp` | 115 | `>` -> `>=` | `avg_t = n > 0 ? ...` | `n` (process count) is positive non-zero integer; `n > 0` vs `n >= 0` evaluates identically for n >= 1. |
| `Scheduler.hpp` | 130 | `>` -> `>=` | `queue.clear()` check | Queue initialization check for positive process count. |
