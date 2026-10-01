# Decisions (append-only)

Format: YYYY-MM-DD | decision | reason | approved by

2026-10-01 | Added CandidateDraft model separating LLM raw output from system-managed Candidate model | LLM output must not include system-assigned IDs or metadata | Human (R-01)
2026-10-01 | Added line number constraint start_line >= 1 and start_line <= end_line on Finding | Prevent invalid source spans in detector findings | Human (R-01)
2026-10-01 | Added positivity and non-negativity constraints on WorkloadResult fields (n > 0, runs > 0, times >= 0) and VerifyReport speedup > 0 | Prevent invalid timing or benchmark results | Human (R-01)
2026-10-01 | Enforced strict conditional requirement on rejected_reason: required when equivalent=False, must be None when equivalent=True | Guarantee unambiguous verification report statuses | Human (R-01)
2026-10-01 | DECISION D-1: speedup_at_max_n is float | None (>0 when set), required when equivalent=True, None when equivalent=False; workloads may be empty only when equivalent=False; crossover_n > 0 when set | Handle rejected candidates without speedup and enforce positive crossover bounds | Human (D-1)
