# LANE E: study, docs, and the scenario suite (S-11, S-12)

You are lane E of a parallel sprint on repo verifieds. Read .agent/SPRINT.md first.
Owned paths: verifieds/study/**, tests/test_study*.py, tests/fixtures/study/**, README.md, docs/**, tests/test_readme.py, results/**
Deadlines (clock minutes): study core 30, docs draft 50, final 57

RULES FOR EVERY LANE (read fully)
A1 Truth: never type command output into a file. Evidence only from `PY tasks.py evidence --task <ID>` (needs dirty=0, exit=0). Never claim what you did not run.
A2 Dependencies: standard library plus pydantic, pytest, pytest-cov, ruff, mypy, vulture; lane D alone adds `mcp` (pinned). Nothing else (the `imports` step enforces it).
A3 No dead code, no stubs, no TODO, no speculative features, no commented-out code. A4 Build only what your cards list. A6 Never weaken a gate or delete a test; never edit an expected value without a DECISIONS.md entry.
A7 sim/src stays free of std containers and sorts. A8 Read installed APIs before use. A9 Write BLOCKED.md and stop if a rule would be violated, 5 repair iterations fail, or the spec contradicts itself.
You may not edit files you do not own (table in .agent/SPRINT.md). To change a shared contract, send a CHANGE message to COMMANDER and wait for the reply.

ENVIRONMENT
Windows 11 PowerShell. Your worktree is C:\dev\wt-<LANE> on branch lane/<LANE>. PY = C:\dev\verifieds\.venv\Scripts\python.exe. Run every command from your worktree root. Preflight: `PY -c "import verifieds;print(verifieds.__file__)"` must print a path inside YOUR worktree; if not, set $env:PYTHONPATH to your worktree root and recheck.
Inner loop: `PY -m pytest <your test files> --no-cov -x -q`, then `PY -m ruff check .`, `PY -m ruff format .`, `PY -m mypy --strict verifieds`. Full gate only at merge: `PY tasks.py py` and, at lane end, `PY tasks.py evidence --task <ID>`.
Clock: `PY sprint.py clock` prints minutes since sprint start. Check it at the start of every loop iteration.

NO STUBS, INTERFACES FIRST
Other lanes are being built at the same time. Code against verifieds/contracts.py (injected callables and the Proposer protocol). Your tests use FAKES that live only in tests/. Never import another lane's package inside production code unless that lane has sent you READY and its commit is on origin/integration.

THE BUS (talk to other lanes)
`PY sprint.py say --sender <LANE> --to <LANE|ALL|COMMANDER> --kind <READY|NEED|CHANGE|REVIEW_REQUEST|REVIEW_RESULT|BLOCKED|DONE|HALT> --text "<=12 lines"`
`PY sprint.py inbox --me <LANE>` prints new messages. Read it at the start of every loop iteration and before every merge. A HALT message means: stop merging, finish your current repair loop, wait for COMMANDER.
READY messages must contain the commit sha on origin/integration and the exact public function names.

PEER REVIEW RING (reviewer of A is E, of B is A, of C is B, of D is C, of E is D)
When your lane is locally green: send REVIEW_REQUEST to your reviewer with branch name and `git diff origin/integration...HEAD --stat`. Meanwhile continue with your next card. When asked to review: spend at most 8 minutes; run their tests, read the diff against these checks: (1) every acceptance item has a test that would fail if the code were wrong; (2) no unused code, TODO, stubs; (3) no std containers in sim/src; (4) dependencies within A2; (5) Windows handling; (6) no hand-typed evidence. Send REVIEW_RESULT PASS or CHANGES with at most 5 numbered items. If no reviewer answers within 8 minutes, merge anyway and write "UNREVIEWED" in your handoff.

MERGE PROCEDURE (repeat for each merge; never force-push)
1. `git fetch origin; git rebase origin/integration`, resolve conflicts (only in files you own), run `PY tasks.py py` and fix.
2. `PY sprint.py lock` (if LOCKED, wait 20 s and retry). `git fetch origin`; if origin/integration moved, rebase again and rerun ruff, mypy, vulture and your own tests only. `git push origin HEAD:integration`. `PY sprint.py unlock`. Hold the lock for under 2 minutes.
3. Send READY (or DONE) to ALL with the sha. Do not wait for CI; COMMANDER watches it.

TIME LADDER (minutes from `PY sprint.py clock`)
At 45: drop every card marked STRETCH. At 52: drop every card marked OPTIONAL and finish what is green. At 57: merge what is green, write your handoff with a NOT DONE list, send DONE. Never leave work unmerged because it is incomplete: merge the green subset.

HANDOFF
For each finished card write .agent/state/handoffs/<ID>.md: files changed, tests, evidence log path, "Open risks" (list what you could not verify), "NOT DONE" (anything dropped). Do not edit BOARD.md or graph.json.


YOUR CARDS

CARD E0 (required, first 3 minutes) The commander already added tests/reference_scheduler.py and tests/test_scenarios_sim.py (45 tests pass on Linux). Run them on Windows. If anything fails, find the cause: a failure is a real simulator bug or a Windows issue (newlines, .exe), not a reason to edit the expected values. Report results to COMMANDER via the bus.

CARD E1 (required; inject detect, compile_fn, compare; use the real simulator via subprocess for correctness checks)
N8 S-11 study (verifieds/study; python -m verifieds.study --models a,b [--dry-run]; csv and statistics only)
 - For each of the 5 policies and each model: ask Ollama for a single-file C++ program that reads the S-03 batch file (argv[1]) and prints the same JSON as sim_cli; compile; record compiled, correct (matches sim_cli on Set A and Set B), findings (rule ids), time_ratio versus sim_cli backend=heap at n=10000. Unavailable Ollama or model error becomes a row with status unavailable, never a crash. Write results/study.csv and results/summary.md (counts and medians).
 - --dry-run uses 2 canned samples in tests/fixtures/study/ (one correct but naive, one wrong), time_ratio = n/a, deterministic. Tests: two dry runs give byte-identical CSV; the correct sample compiles and is correct; the wrong one is marked incorrect.

CARD E2 (required, after all lanes are merged or at clock 50) docs
N9 S-12 docs
 - README.md: what it is, Windows install (the winget commands), `PY tasks.py` usage, run the simulator, the pipeline, MCP registration, the study, limits (not a sandbox; equivalence is tested, not proven; the detector is a lightweight scanner, not a full parser).
 - docs/REPORT_OUTLINE.md: outline mapped to the rubric in the project spreadsheet (each criterion -> file or demo), plus the novelty claims with the caveat "literature check not exhaustive".
 - tests/test_readme.py: every `$ python tasks.py <command>` line in README names a real subcommand; every path mentioned in backticks exists.
 README lists only commands and claims that exist on origin/integration. Add docs/CLAIMS.md mapping each README claim to a test function and a test that fails if a mapped test does not exist.

