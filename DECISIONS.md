# Architecture & Scope Decisions (DECISIONS.md)

| Decision ID | Description |
|---|---|
| D-1 | `speedup_at_max_n` is `float \| None` (> 0.0 when set), required when `equivalent` is true, `None` when false. `workloads` may be empty only when `equivalent` is false. `crossover_n` > 0 when set. |
| D-2 | BST and MinHeap: BST ignores duplicate keys on insertion. MinHeap maintains FIFO ordering for equal priority keys. |
| D-3 | Scheduling ties in FCFS, SJF, SRTF, and PRIORITY are broken by process ID (`pid`) ascending. |
| D-4 | Candidate diffs are applied to isolated workspace copies in temp directories using git patch apply. |
| D-5 | Performance benchmark runner computes the median execution time over 3 runs using fixed random seeds. |
| D-6 | Proposer prompt uses `DATA_BLOCK` delimiter, strictly forbids `<code>` tags and schema inline snippets, and forbids extra keys (such as `id` or `finding_id`). |
| D-7 | Promote proposal P-01 (workload-adequacy score via mutation of the C++ sources) into scope as node Q4, with a new Pydantic model `AdequacyReport` and an exported schema. |
| D-8 | A test oracle independent of the C++ code (`tests/reference_scheduler.py`) is the source of truth for scheduling expectations; never derive expected values from `sim_cli` output. |
