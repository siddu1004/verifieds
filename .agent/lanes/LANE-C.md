# LANE C: pipeline, wiring, pipeline scenarios (S-08) and adequacy

You are lane C of a parallel sprint on repo verifieds. Read .agent/SPRINT.md first.
Owned paths: verifieds/pipeline/**, verifieds/wiring.py, verifieds/adequacy/**, verifieds/schemas/models.py and schemas/*.json (only for AdequacyReport), tests/test_pipeline*.py, tests/test_scenarios_pipeline.py, tests/test_adequacy*.py
Deadlines (clock minutes): core local green 25, wiring merged 42, final 57

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

CARD C1 (required; code against contracts.py with fakes; A and B are not merged yet)
N5 S-08 pipeline (verifieds/pipeline)
 - Proposer interface propose(finding, code) -> list[CandidateDraft]; OllamaProposer implements it. run_pipeline(source_dir, file, proposer, workspace) -> list[VerifyReport]: detect; propose; the pipeline (not the model) assigns Candidate ids (sha256 of finding id + diff, 16 hex); copy source_dir to a temp dir, apply the diff with `git apply` (reason "diff does not apply" on failure), compile both, harness.compare. Never run anything outside temp dirs.
 - Tests with a fake proposer, building diffs with difflib.unified_diff on the real file text: (1) flipping kDefaultBackend in sim/src/Config.hpp from "array" to "heap" is accepted, speedup_at_max_n > 1; (2) a diff that breaks tie-breaking is rejected with an output-mismatch reason; (3) a diff that does not apply is rejected; (4) a diff that causes a compile error is rejected with the compiler message.
 Dependency injection (no imports of detector or harness inside pipeline code): run_pipeline(source_dir, file, proposer, workspace, *, detect, compile_fn, compare, sizes=(100,1000,10000), runs=7, seed=1234) and make_verify_diff(compile_fn, compare, workspace, sizes, runs, seed) -> VerifyDiffFn.

CARD C2 (required, starts when READY from A and B are on origin/integration)
 Create verifieds/wiring.py binding the real detect_file, compile_program and compare, exposing build_verify_diff(workspace) and default_detect. Then run the card Q2 scenarios below against the REAL detector and harness. Send READY to D and E when wiring is merged.

CARD C3 (required) Q2 scenarios
Q2 Pipeline scenarios (tests/test_scenarios_pipeline.py, fake proposer; diffs built with difflib on real file text)
 P-A correct rewrite (kDefaultBackend array -> heap) accepted, speedup_at_max_n > 1.
 P-B tie-break mutant: remove the pid component from the ReadyEntry comparison. Must be rejected with an output-mismatch reason. Also assert the generated workloads contain at least 10 equal-key pairs at n=100 (otherwise this mutant would wrongly survive: this checks workload adequacy).
 P-C quantum off-by-one mutant in round_robin: rejected (needs an RR workload; extend generate_workload with `policy` and `quantum` parameters if missing, minimal change, covered by tests).
 P-D fast-but-wrong candidate that prints a fixed JSON: rejected. P-E candidate that is faster only at large n: crossover_n is greater than the smallest size (use a synthetic pair of programs). P-F candidate with a compile error and one with an infinite loop: rejected with the right reasons within the timeout.
 L-scenarios with a fake Ollama server (stdlib http.server): L-1 prose instead of JSON, L-2 JSON inside markdown fences, L-3 a 5 MB body, L-4 extra keys (id, finding_id), L-5 empty candidates list, L-6 response slower than the timeout, L-7 connection refused. Each gives a typed error or an empty result; none crashes or hangs; L-2 is either parsed or rejected, and the test documents which.

CARD C4 (STRETCH, only if clock < 45 when you reach it)
Q4 Workload-adequacy score (D-7). Package verifieds/adequacy, command `PY -m verifieds.adequacy --source sim/src --files Scheduler.hpp,ReadyQueue.hpp --seed 1`
 - Mutation sites: a fixed list of textual operator swaps found by regex in the listed files (< <-> <=, > <-> >=, == <-> !=, + 1 -> + 0, - 1 -> - 0, && <-> ||), ordered by file, line, column; cap at 60 mutants.
 - For each mutant: copy the source tree to a temp dir, apply the swap, compile; compile failure = status invalid (not counted). Otherwise run harness.compare(original, mutant) for each of the 5 policies (workloads generated per policy); killed if any policy reports non-equivalence, else survived.
 - AdequacyReport (Pydantic, add to schemas export): mutants (list of {file, line, from, to, status}), killed, survived, invalid, score = killed/(killed+survived). State plainly in the output and README: survivors may be equivalent mutants; the score is a lower-bound indicator of how well the workloads can detect behavioural change, not a proof.
 - Loop: if score < 0.85, inspect survivors, improve the workload generator (tie-heavy mode, priority-heavy mode, bursty arrivals) in a minimal documented way, and re-run; at most 3 loops. If still below 0.85 write each survivor with a reason into docs/ADEQUACY.md; do not lower the threshold.
 - Tests: deterministic report for a fixed seed; a synthetic weak workload lets a known mutant survive and a richer workload kills it; invalid mutants are excluded from the score.

