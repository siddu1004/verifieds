# LANE B: harness (S-06)

You are lane B of a parallel sprint on repo verifieds. Read .agent/SPRINT.md first.
Owned paths: verifieds/harness/**, tests/test_harness*.py
Deadlines (clock minutes): local green 22, merged 28, final 57

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

CARD B1 (required; send READY for generate_workload FIRST, by minute 15, because lanes C and E need it)
N4 S-06 harness (verifieds/harness)
 - compile(source_dir, main_file, out_path): g++ -std=c++20 -O2 -I<source_dir>, typed error with compiler output.
 - generate_workload(n, seed, path): S-03 batch text (policy=SJF), arrival uniform in [0, n//4], burst 1-20, priority 1-10, unique pids, deterministic per seed.
 - run(binary, args, timeout_s, memory_limit_mb=None): timeout and kill via subprocess; wall time via perf_counter; typed errors (timeout, nonzero exit). memory_limit_mb not None on Windows raises NotImplementedError (tested); on Linux uses resource.setrlimit (test skipped on win32).
 - compare(original_bin, candidate_bin, sizes=(100,1000,10000), runs=7, seed=1234, timer=perf_counter): per size generate a workload, run both `runs` times, hash normalised stdout. Equivalent only if every hash matches. Return a VerifyReport (D-1 schema): rejected_reason strings "output mismatch at n=..", "timeout at n=..", "compile error"; workloads with medians; speedup_at_max_n only if equivalent; crossover_n = smallest size where the candidate median is lower AND its [min,max] range does not overlap the original's at that size and every larger size, else null. sizes, runs and the timer are parameters.
 - Tests with small generated C++ programs in a temp dir: linear vs quadratic work with identical output (right ordering, speedup > 1, right crossover); noisy injected timer gives crossover null; different output is rejected with the right reason; an infinite loop is killed by the timeout; doubling n roughly quadruples the quadratic program and doubles the linear one (loose bounds); sim_cli backend=array (original) vs backend=heap (candidate) is equivalent and heap wins at the largest size.
 Public API (exact names, exported from verifieds/harness/__init__.py): compile_program(source_dir: Path, main_file: str, out_path: Path) -> Path (a CompileFn); generate_workload(n: int, seed: int, path: Path, policy: str = 'SJF', quantum: int | None = None, ties: bool = False) -> None (ties=True draws bursts and priorities from a tiny set so many keys are equal); compare(original, candidate, candidate_id, sizes, runs, seed, *, timer=time.perf_counter, policy='SJF', quantum=None) -> VerifyReport (positional order matches CompareFn). Replace the card's `compile(...)` name with compile_program.

