# SPRINT PLAN: finish VerifiedDS in about 60 minutes with parallel agents

Honest status: the 60-minute figure is a plan, not a promise. It depends on how fast your agents run and on whether Antigravity can run several agents at once. If lanes are not launching by minute 10, fall back to sequential mode (master prompt) and treat the lane files as the task list. The time ladder guarantees a merged, working core at minute 60, not every optional feature.

## Graph (work and messages)

    T+0   COMMANDER: install pack, apply tasks.py patch, quick gate, push, worktrees, launch lines
            |
    +-------+--------+---------+----------+---------+
    v                v         v          v         v
  LANE A           LANE B    LANE C     LANE D    LANE E
  detector         harness   pipeline   MCP+safe  scenarios, study, docs
  (S-05)           (S-06)    (S-08)     (S-09/10) (S-11/12)
    |  READY          | READY    ^  fakes   ^ fakes    ^ fakes
    +-----------------+--------> wiring (C, ~T+30) -READY-> D, E wire real parts (~T+42)
    reviews: E->A, A->B, B->C, C->D, D->E (ring, 8 minutes each)
    T+55  COMMANDER: merge status, `PY tasks.py evidence --task RC` on integration, CI, tag v0.1.0-rc1

## Critical path and why it fits
Detector and harness run in parallel (about 22 to 28 min). Pipeline, MCP and study are built against contracts.py with fakes in the same window, so they do not wait. Wiring takes about 12 minutes after A and B merge. Docs run last and only describe what exists.

## Ownership (no two lanes edit one file)
| Path | Owner |
|---|---|
| verifieds/detector, verifieds/rules, tests/fixtures/<rule> | A |
| verifieds/harness | B |
| verifieds/pipeline, verifieds/wiring.py, verifieds/adequacy, schemas/models.py + schemas/*.json | C |
| verifieds/mcp_server, pyproject.toml + DEPS.md (mcp pin only) | D |
| verifieds/study, README.md, docs, results | E |
| tasks.py, sprint.py, verifieds/contracts.py, .agent/state/BOARD.md, graph.json, CI yaml | COMMANDER |

## Interface table (frozen at minute 0 in verifieds/contracts.py)
| Name | Shape | Provided by |
|---|---|---|
| Proposer.propose | (Finding, code_snippet) -> list[CandidateDraft] | existing OllamaProposer |
| DetectFn | (Path) -> list[Finding] | A: verifieds.detector.detect_file |
| CompileFn | (source_dir, main_file, out_path) -> Path | B: verifieds.harness.compile_program |
| CompareFn | (orig_bin, cand_bin, candidate_id, sizes, runs, seed) -> VerifyReport | B: verifieds.harness.compare |
| VerifyDiffFn | (source_dir, main_file, diff, candidate_id) -> VerifyReport | C: pipeline.make_verify_diff |
Only the COMMANDER changes contracts.py (lanes send CHANGE).

## Message kinds
READY (interface is on origin/integration, with sha), NEED (ask a lane for something), CHANGE (contract change request to COMMANDER), REVIEW_REQUEST, REVIEW_RESULT, BLOCKED, DONE, HALT (COMMANDER stops merges after a red CI).

## Scope-cut ladder (if time runs out, drop in this order)
1. C4 adequacy score (STRETCH). 2. D3 safety bullets beyond three. 3. E1 real-model study run (keep the dry run). 4. README polish. Never drop: A1, B1, C1-C3, D1, E0, E1 dry run, a minimal README.

## What I validated before writing this
verifieds/contracts.py and tests/test_contracts.py pass ruff, mypy --strict, vulture and pytest in the current repo. tests/test_scenarios_sim.py (21 tests: hand-computed scenarios, 100-workload oracle differential, six metamorphic properties on 40 workloads, a 3,000-process backend check) passes against the real sim_cli on Linux. sprint.py (bus, lock, clock) was exercised end to end. I did not run any of this on Windows.

## Launch lines


    You are LANE A. Open C:\dev\wt-A. Read .agent\lanes\LANE-A.md and .agent\SPRINT.md and execute your cards exactly. Do not ask questions.
    You are LANE B. Open C:\dev\wt-B. Read .agent\lanes\LANE-B.md and .agent\SPRINT.md and execute your cards exactly. Do not ask questions.
    You are LANE C. Open C:\dev\wt-C. Read .agent\lanes\LANE-C.md and .agent\SPRINT.md and execute your cards exactly. Do not ask questions.
    You are LANE D. Open C:\dev\wt-D. Read .agent\lanes\LANE-D.md and .agent\SPRINT.md and execute your cards exactly. Do not ask questions.
    You are LANE E. Open C:\dev\wt-E. Read .agent\lanes\LANE-E.md and .agent\SPRINT.md and execute your cards exactly. Do not ask questions.
