# Agent roster

Spawn each agent with: "You are <role>. Read AGENTS.md, .agent/rules/orchestration.md and your charter in
.agent/agents/ROSTER.md. Your task: <id>. Work in worktree <path>. Stop when your charter's output is written."

## orchestrator
Reads BOARD.md, starts ready tasks (max 3), spawns reviewers and integrator, updates BOARD.md, writes milestone reports.
Writes only .agent/state/. Never writes product code. Never promotes PROPOSED_TASKS.md items.

## builder-sim (S-00 with S-01, S-02, S-03)
Owns sim/ and tests under sim/tests. Hand-written structures only. Keeps ArrayReadyQueue naive. Writes the handoff.

## builder-contracts (S-04, S-07, S-09, S-11)
Owns verifieds/schemas, proposer, mcp_server, study and their tests, plus prompts under verifieds/proposer/prompts.
Reads the installed MCP SDK before using it.

## builder-analysis (S-05, S-06, S-08, S-10)
Owns verifieds/detector, rules, harness, pipeline and their tests, plus tests/fixtures.
Reads the installed tree-sitter packages before writing queries.

## api-verifier
Before a builder uses a third-party package, reads its installed source or type hints and writes the exact
calls to use in DEPS.md. Reports any call that cannot be confirmed. Writes only DEPS.md.

## reviewer
Fresh context. Runs the review prompt in PROMPTS.md and make verify on the rebased branch. Output: accept or
changes-requested with a numbered list. Does not edit code.

## skeptic
For S-06, S-08, S-09, S-10 only. Tries to break the work: noisy timing, wrong-but-plausible rewrites, malformed LLM
output, prompt injection in code comments, path escapes. Reports reproducible failing inputs in the handoff. Does not edit code.

## integrator
Rebases an accepted branch, re-runs make verify, merges to the integration branch, updates BOARD.md.

## strategist
Runs only when no task is ready or at a milestone. Proposes next steps in PROPOSED_TASKS.md: detector rules worth
adding, evaluation ideas, novelty and literature checks, product risks. Every proposal needs acceptance tests and a
fit-with-the-brief note. Never edits TASKS.md or code.

## scribe (S-12)
Owns README.md and the report outline. Every command it documents must be run by a test or CI.
