# LANE A: detector (S-05)

You are lane A of a parallel sprint on repo verifieds. Read .agent/SPRINT.md first.
Owned paths: verifieds/detector/**, verifieds/rules/**, tests/test_detector*.py, tests/fixtures/<rule_id>/**
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

CARD A1 (required)
N3 S-05 detector (verifieds/detector; pure Python, D-3)
 - Scanner: strip comments and string literals while keeping line numbers; tokenise with the re module; find for/while loops and their bodies by brace matching (also single-statement bodies); expose loops with start_line, end_line, header tokens, body tokens, nested loops.
 - Rule = verifieds/rules/<rule_id>.json (rule_id, adt, impl, complexity_before, description) + <rule_id>.py exposing match(source_view) -> list of (start_line, end_line, evidence). Loader fails if the json, the matcher, or tests/fixtures/<rule_id>/ with pos_*.cpp and neg_*.cpp is missing.
 - Rules: array-queue-front-removal (loop body shifts elements left: X[i] = X[i+1] with the loop variable, or .erase(X.begin()) inside a loop); linear-min-extract (loop comparing X[i] < X[best] and assigning best = i); adjacent-swap-sort (nested loops comparing X[j] with X[j+1] and swapping); linear-search-in-loop (nested loop comparing X[j] == key with return or break inside).
 - Each rule has at least 2 positive fixtures in different styles (for and while) and 2 negative ones. Positive: exactly 1 finding with correct lines. Negative: 0.
 - Output list[Finding] (S-04 schema); id = first 16 hex chars of sha256 of "rule_id|file|start|end"; sorted by file then line. Required: sim/src/ArrayReadyQueue.hpp yields findings from linear-min-extract and array-queue-front-removal; HeapReadyQueue.hpp and MinHeap.hpp yield none from those two rules.
 Export `detect_file` (a DetectFn: Path -> list[Finding]) from verifieds/detector/__init__.py. When merged send READY to ALL naming it.

CARD A2 (OPTIONAL, after merging A1): review lane B's diff if asked; add 2 extra negative fixtures per rule taken from real sim/src code (HeapReadyQueue.hpp, MinHeap.hpp, Sort.hpp) to prove there are no false positives there.

