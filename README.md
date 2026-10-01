# VerifiedDS

> Detects suboptimal data-structure choices in C++ code, proposes better ones via a local
> LLM (Ollama), and accepts a change **only** if it is proven equivalent and measurably faster.

## Build status

| Gate | Status |
|---|---|
| Python (ruff · mypy · vulture · pytest 90 %) | ✅ green |
| C++ (cmake · g++ · cppcheck · CTest) | ⚠️ CI only — install cmake/g++/cppcheck locally first |
| CI (GitHub Actions — ubuntu-latest) | defined in `.github/workflows/verify.yml` |

## Task progress

| Task | Description | Status |
|---|---|---|
| **S-00** | Scaffold (CMake, pyproject, CI) | 🔍 review |
| S-01 | Core C++ structures | 🟡 ready |
| S-02 | Scheduler engine | ⬜ todo |
| S-03 | CLI | ⬜ todo |
| **S-04** | Pydantic schemas | 🔍 review |
| S-05 | Detector (tree-sitter) | ⬜ todo |
| S-06 | Harness (timing + equivalence) | ⬜ todo |
| **S-07** | Proposer (Ollama client) | 🟡 ready |
| S-08 | Pipeline (end-to-end) | ⬜ todo |
| S-09 | MCP server | ⬜ todo |
| S-10 | Safety tests | ⬜ todo |
| S-11 | Study script | ⬜ todo |
| S-12 | README + report | ⬜ todo |

## Setup

### Prerequisites
- Python ≥ 3.11
- g++ with C++20 support
- CMake ≥ 3.20
- cppcheck
- [Ollama](https://ollama.com) with a coder model pulled (e.g. `ollama pull qwen2.5-coder`)

### Install
```bash
pip install -e ".[dev]"
```

### Verify
```bash
make tools-check   # check all tool versions (non-fatal for missing C++ tools)
make verify-py     # Python lint + type check + tests
make verify-sim    # C++ build + sanitizers + ctest
make verify        # both
```

## Windows
The Makefile uses Unix shell commands. Use **WSL2** (recommended) or **MSYS2**, and
run `make tools-check` first. Python tools work natively via `python -m <tool>`.

## Parallel (orchestrated) mode
Use the Orchestrator kickoff in `PROMPTS.md`. Agents coordinate through `.agent/state/`
and git worktrees. Humans approve at milestone gates M1–M5; agents never merge to main.

## Limits
The gates catch dead and untested code but cannot guarantee correctness. Equivalence
is checked by testing, not proof. The detector covers four rules in this version.
Resource limits in the harness are not a full sandbox.

