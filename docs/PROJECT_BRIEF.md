# Project brief

## Problem
Correct code is often inefficient in ways tests never reveal (for example a ready queue
built on an unsorted array: every dequeue scans the whole array). VerifiedDS finds such
choices, proposes a better structure with a free local LLM (via Ollama), and accepts a
change only if (1) the output is identical to the original and (2) measurement shows it
is faster at scale. It reports the crossover size n* above which the change pays off.

## Course version scope
- sim/: CPU Process Scheduling Simulator in C++20 with hand-written DynArray, Stack,
  circular Queue, MinHeap and heap sort, BST with in/pre/post-order traversal.
  Policies: FCFS, SJF (non-preemptive), SRTF, Round Robin, Priority (non-preemptive).
  Two ready-queue backends behind one interface: ArrayReadyQueue (linear min-scan) and
  HeapReadyQueue. Ties are broken by arrival time, then pid.
- verifieds/: Python package: detector (pure-Python token scanner per D-3), harness, proposer, MCP server, study.
- Detection is limited to four rules (JSON metadata + Python matcher): array-queue-front-removal, linear-min-extract,
  adjacent-swap-sort, linear-search-in-loop. Do not add rules without a new task.

## Data shapes (single source: Pydantic models, exported to schemas/*.json)
- Finding: id (stable hash of rule_id, file, span), rule_id, file, start_line, end_line,
  adt (queue | stack | priority_queue | list | sort | search), impl, complexity_before, evidence.
- Candidate: id, finding_id, strategy, diff (unified diff), expected_complexity_after, risks (list).
- VerifyReport: candidate_id, equivalent (bool), rejected_reason (optional), workloads
  (list of {n, original_ms_median, candidate_ms_median, runs}), speedup_at_max_n,
  crossover_n (integer or null).

## Principles
- LLM proposes, harness decides. Never present an unverified suggestion as a result.
- Verification by testing is not proof of equivalence; reports must say "equivalent on tested workloads".
- Resource limits in the harness are not a full sandbox; the README must say so.
- Rules, prompts and schemas are data files so a later TypeScript core can reuse them unchanged.

## Out of scope for this pack
TypeScript core, Docker sandbox, VS Code extension, GitHub Action, billing. Write those
tasks in the same format only after the tasks in TASKS.md are reviewed and accepted.
