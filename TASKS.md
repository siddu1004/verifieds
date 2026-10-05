# Task backlog (strict order; one task per session)

Every task also requires `make verify` to pass.

## S-00 Scaffold
Create Makefile targets' prerequisites: sim/CMakeLists.txt (flags from .agent/rules/quality.md,
ENABLE_SANITIZERS option, test runner via CTest), pyproject.toml (Python >= 3.11, ruff, mypy,
vulture, pytest, pytest-cov), package verifieds/, DEPS.md, .github/workflows/verify.yml that runs make verify.
Acceptance: one smoke test per language; `make verify` passes; CI file runs the same command;
`make tools-check` (already in the Makefile) prints every tool's version and keeps working.

## S-01 Core structures (sim/src)
DynArray, Stack, circular Queue, MinHeap with heap sort, BST (insert, search, delete, in/pre/post-order).
Acceptance: empty pop and peek handled; capacity growth; duplicates; BST delete with 0, 1 and 2 children;
heap sort equals a reference sort on 1,000 seeded inputs (reference lives in tests only).

## S-02 Scheduler engine
Process{pid, arrival, burst, priority}; ReadyQueue interface with ArrayReadyQueue and HeapReadyQueue;
FCFS, SJF, SRTF, Round Robin (quantum), Priority; waiting, turnaround and response times; Gantt list.
ArrayReadyQueue must stay deliberately naive (linear min-scan). It is the test subject for S-05 and S-08 and must not be optimised.
Acceptance: hand-computed textbook schedules match exactly; both backends give identical schedules for
1,000 seeded random workloads; ties broken by arrival then pid.

## S-03 CLI
Menu CLI and `--batch <json>` mode: add, delete, update, search (BST by pid), display, sort (own sort),
run policy, context-switch history (Stack).
Acceptance: scripted-stdin golden outputs; batch JSON in and JSON out; invalid input rejected with a message and no crash.

## S-04 Schemas
Pydantic models Finding, Candidate, VerifyReport per docs/PROJECT_BRIEF.md; export to schemas/;
add `python -m verifieds.schemas.export --check` and append it to verify-py in the Makefile.
Acceptance: round-trip tests; invalid payloads rejected; a stale schema file makes --check fail.

## S-05 Detector
Pure-Python token scanner (D-3), rule loader, the four rules; each rule is verifieds/rules/<rule_id>.json metadata + <rule_id>.py matcher.
Acceptance: each rule's positive fixture gives exactly 1 finding with the correct line span and its negative
fixture gives 0; the loader test fails any rule missing a fixture; sim/src/ArrayReadyQueue.hpp yields findings from linear-min-extract and array-queue-front-removal; HeapReadyQueue.hpp and MinHeap.hpp yield none.

## S-06 Harness
Compile original and candidate (g++ -O2), run seeded workloads at n = 10^2, 10^3, 10^4, compare output
hashes, time with the median of k runs, compute crossover n*, enforce timeouts; memory limits on Windows raise NotImplementedError (D-4).
Runs per size is configurable (default 7). crossover_n is null unless the candidate's timing range does not overlap the original's at the neighbouring sizes.
Acceptance: synthetic O(n) vs O(n^2) programs give the correct ordering and n*; a noisy-timing test yields crossover_n null; doubling-n metamorphic test;
a non-equivalent candidate is rejected; a runaway program is killed.

## S-07 Proposer
Proposer interface and Ollama client (HTTP to the local Ollama server), strict JSON parsing, one retry;
model name comes from config, never hard-coded.
Acceptance: tests use an in-test fake HTTP server (stdlib) returning valid, malformed and empty responses;
malformed twice gives a typed error.

## S-08 Pipeline
finding to proposals to harness to accept or reject to VerifyReport.
Acceptance: end to end on the naive simulator with a fake proposer returning the heap rewrite: accepted with
speedup above 1 and n* reported; with a wrong rewrite: rejected with a reason.

## S-09 MCP server
stdio server using the official Python MCP SDK (read its installed API first). Tools: analyze_file,
propose_candidates, verify_candidate, explain_change, each with an output schema from S-04; static tool descriptions.
Configure vulture's ignore_decorators in pyproject for the SDK's tool-registration decorator, with a one-line justification comment, instead of per-function suppressions (check the installed vulture docs for the exact option).
Acceptance: an in-process client test lists tools and validates structured outputs against schemas; paths outside
the workspace are rejected; explain_change uses only numbers present in the report.

## S-10 Safety tests
Acceptance: a fixture whose comment instructs the model to run a shell command is ignored; the harness never
runs code outside its working directory; secrets from .env never appear in prompts or logs. README states that
resource limits are not a full sandbox.

## S-11 Study script
For each of the 5 policies and each configured model: generate a scheduler, run the pipeline, write CSV and
summary statistics (pandas, scipy); seeds fixed.
Acceptance: a dry run on 2 canned samples produces identical CSV twice; the command to run on real models is documented.

## S-12 README
Install, run, MCP registration, limits, and a report outline mapped to the course rubric.
Acceptance: every command in the README is executed by a test or the CI workflow.
