# Orchestration protocol

Agents have separate contexts and coordinate only through files in .agent/state/ and git. No agent relies on another agent's memory.

## State files
- BOARD.md: one row per task: id, deps, owner role, status, branch, last make verify result.
  Statuses: todo, ready, in-progress, review, changes-requested, accepted, blocked.
- handoffs/S-0X.md: the builder's report (files changed, tests, make verify result, risks).
- DECISIONS.md: append-only log of decisions (date, decision, reason). Needed for any schema change after S-04.
- PROPOSED_TASKS.md: ideas from the strategist. Only a human promotes an item into TASKS.md.
- MILESTONE-Mx.md: summary written by the orchestrator at each human gate.

## Rules
1. At most 3 builders run at once. Only tasks whose dependencies are accepted may start.
2. Each task runs in its own git worktree and branch (task/S-0X) created from the integration branch.
3. Builders write only inside their owned paths (ROSTER.md). Changes to Makefile, pyproject.toml, CMake files
   or DEPS.md go in small commits that are rebased on integration before review.
4. The reviewer is never the builder of that task and starts with a fresh context.
5. Merge condition: reviewer accepts AND make verify is green on the rebased branch. Only the integrator merges,
   and only into the integration branch, never into main.
6. A task that fails review or verify three times becomes blocked with a BLOCKED.md. Do not loop further.
7. After S-04 is accepted the schemas are frozen: changes need a DECISIONS.md entry and human approval.

## Autonomy levels
- L1 (inside a task): builders choose their own implementation. They may not expand scope.
- L2 (finding next steps): when no task is ready, the strategist may append items to PROPOSED_TASKS.md in the
  TASKS.md format (goal, acceptance tests, deps, why it fits the brief). Nothing there is executed until a human promotes it.
- L3 (integration): agents may merge to the integration branch after review. Merging to main is human-only.

## Human gates (orchestrator stops and writes MILESTONE-Mx.md)
M1 after S-00. M2 after S-02 and S-04 (core and schema freeze). M3 after S-08 (pipeline works end to end).
M4 after S-10. M5 after S-12 (final).

## Stop immediately and write BLOCKED.md if
A hard rule in AGENTS.md would be violated, a library API cannot be verified from installed sources, a secret
appears in a prompt or log, or three cycles pass with no progress.
