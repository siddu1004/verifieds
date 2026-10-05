# VerifiedDS

VerifiedDS detects data-structure and algorithm bottlenecks in C++ projects, proposes optimizations using a local LLM (Ollama), and accepts changes only if verified equivalent and measurably faster. It does not generate mathematical proofs of program equivalence and relies on workload execution to reject incorrect candidate patches.

## Quick Start & Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## System Diagnostics & Smoke Test

Before running VerifiedDS, run the environment diagnostics tool to check g++ compiler presence, workspace writability, Ollama reachability, and model presence:

```powershell
python -m verifieds.doctor
```

After running `doctor`, you can perform a live end-to-end smoke check and candidate verification on any C++ source file:

```powershell
python -m verifieds.smoke --file sim/src/ReadyQueue.hpp --verify
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

## Worked Example: MCP Client Tool Call

MCP clients invoke `verify_candidate` using standard MCP tool call RPC payloads:

```json
{
  "name": "verify_candidate",
  "arguments": {
    "project_dir": "sim",
    "main_file": "src/main.cpp",
    "diff": "--- a/sim/src/Config.hpp\n+++ b/sim/src/Config.hpp\n@@ -10,1 +10,1 @@\n-static constexpr Backend kDefaultBackend = Backend::kMinHeap;\n+static constexpr Backend kDefaultBackend = Backend::kBST;\n",
    "candidate_id": "c1"
  }
}
```

## Use It on Your Own Project

To use VerifiedDS on a custom C++ project, create a standalone workload generator script (e.g. `my_project/gen.py`) that accepts parameters `{n}`, `{seed}`, and `{out}` and writes one test input file:

```python
import random
import sys
from pathlib import Path

n, seed, out = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
rng = random.Random(seed)
items = [rng.randint(1, 100000) for _ in range(n)]
out.write_text("\n".join(map(str, items)) + "\n", encoding="utf-8")
```

Then invoke `verify_candidate` via MCP client tool call with `workload_cmd`:

```json
{
  "name": "verify_candidate",
  "arguments": {
    "project_dir": "my_project",
    "main_file": "src/main.cpp",
    "diff": "...",
    "candidate_id": "c1",
    "workload_cmd": "python my_project/gen.py {n} {seed} {out}"
  }
}
```

## Resource Limits & Safety Disclaimer

> [!WARNING]
> Resource limits on Windows (such as memory caps) raise `NotImplementedError` per decision D-4. The harness enforces process timeout limits but does not provide a full OS sandbox.

## Limits

- Equivalence is tested on generated workloads and not proven.
- Resource limits are not a sandbox.
- The detector is a heuristic scanner covering four patterns.
- The current adequacy score is read from `results/adequacy.json`.
- `verifieds/smoke.py` is excluded from automated code coverage requirements and is exercised manually against live Ollama instances.
