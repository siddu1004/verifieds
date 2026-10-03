# Milestone M1 Report

Date: 2026-10-01
Status: PENDING HUMAN APPROVAL

## Summary of Work Completed

### Phase 0: Remediation & Initial Tasks
1. **S-00 Scaffold**:
   - CMake configuration (`sim/CMakeLists.txt`), C++20 standard, strict warnings, sanitizers option, CTest smoke test.
   - `pyproject.toml` targeting Python ≥ 3.11 with dev dependencies, `ruff`, `mypy --strict`, `vulture`, and `pytest-cov` (90% threshold).
   - `Makefile` updated to use `python -m <tool>` for Windows compatibility.
   - `.github/workflows/verify.yml` CI workflow defined.
   - `DEPS.md` populated with exact pins and reasons.

2. **R-00 Repo Hygiene**:
   - Set `build-backend = "setuptools.build_meta"` in `pyproject.toml`.
   - Removed `.vscode/` from git tracking and added to `.gitignore`.
   - Removed unnecessary "Install Ollama" step from `.github/workflows/verify.yml`.
   - Updated `DEPS.md` with exact `==` pins resolved from installed environment (`pydantic==2.13.4`, `ruff==0.16.9`, `mypy==2.3.1`, `vulture==2.16`, `pytest==9.1.1`, `pytest-cov==7.1.0`) and added runtime Ollama note.

3. **S-04 / R-01 Schemas**:
   - Added `CandidateDraft` model separating raw LLM output from system `Candidate`.
   - Added strict validation constraints: `start_line >= 1` & `start_line <= end_line` on `Finding`; `n > 0`, `runs > 0`, `times >= 0` on `WorkloadResult`; `speedup_at_max_n > 0` and conditional `rejected_reason` on `VerifyReport`.
   - Regenerated `schemas/*.json` (including `candidate_draft.json`).
   - Appended entries in `.agent/state/DECISIONS.md`.

4. **S-07 / R-02 Proposer Client**:
   - Implemented `OllamaProposer` returning `list[CandidateDraft]`.
   - Split exception hierarchy into `OllamaUnavailableError` (network/timeout) vs `OllamaParseError` (malformed output).
   - Applied per-request random `DATA_BLOCK_<uuid>` tag wrapping to code snippets and evidence text to prevent tag injection breakout.
   - Added tests for empty response bodies, missing `"response"` keys, and invalid outputs.

5. **Branch Integration**:
   - Merged accepted work into `integration` branch.

## Verification Gate Status

- `make verify-py`: ✅ GREEN (ruff, mypy --strict, vulture, schema export check, 19 tests passing at 95.07% coverage).
- `make verify-sim`: ⚠️ Requires local C++ toolchain (CMake, g++, cppcheck). Runs in GitHub Actions CI environment.

## Action Items for Human Approval

To approve Milestone M1 and allow Phase 1 tasks to commence:
1. **Enable branch protection on `main`** in GitHub settings (require pull request reviews, status checks).
2. **Confirm C++ toolchain installation** (WSL2 or native):
   Run `make tools-check` in your terminal and verify that `cmake`, `g++`, and `cppcheck` are available.
