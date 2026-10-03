# VerifiedDS

VerifiedDS detects data-structure and algorithm bottlenecks in C++ projects, proposes optimizations using a local LLM (Ollama), and accepts changes only if verified equivalent and measurably faster. It does not generate mathematical proofs of program equivalence and relies on workload execution to reject incorrect candidate patches.

## Quick Start & Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## System Diagnostics

Before running VerifiedDS, run the environment diagnostics tool to check g++ compiler presence, workspace writability, Ollama reachability, and model presence:

```powershell
python -m verifieds.doctor
```

After running `doctor`, you can perform a manual live model smoke check on any C++ source file:

```powershell
python -m verifieds.smoke --file sim/src/ReadyQueue.hpp
```

## MCP Server Registration

Register the MCP server stdio interface in your IDE or desktop client with explicit python path and workspace configuration:

```json
{
  "mcpServers": {
    "verifieds": {
      "command": "C:/dev/verifieds/.venv/Scripts/python.exe",
      "args": ["-m", "verifieds.mcp"],
      "env": {
        "VERIFIEDS_WORKSPACE": "C:/dev/verifieds"
      }
    }
  }
}
```

## Worked Example: Simulator

Verify candidate optimizations on the built-in CPU scheduler simulator:

```python
from verifieds.mcp.server import create_mcp_server

server = create_mcp_server()
report = server.tools["verify_candidate"](
    project_dir="sim", main_file="src/main.cpp", diff="...", candidate_id="c1"
)
```

## Worked Example: Custom User Project

Verify a candidate optimization on a generic C++ project using a custom workload_cmd generator:

```python
from verifieds.mcp.server import create_mcp_server

server = create_mcp_server()
report = server.tools["verify_candidate"](
    project_dir="my_project",
    main_file="src/main.cpp",
    diff="...",
    candidate_id="c1",
    workload_cmd="python my_project/gen.py {n} {seed} {out}",
)
```

## Resource Limits & Safety Disclaimer

> [!WARNING]
> Resource limits on Windows (such as memory caps) raise `NotImplementedError` per decision D-4. The harness enforces process timeout limits but does not provide a full OS sandbox.

## Limits

- Equivalence is tested on generated workloads and not proven.
- Resource limits are not a sandbox.
- The detector is a heuristic scanner covering four patterns.
- The current adequacy score is read from `results/adequacy.json`.
