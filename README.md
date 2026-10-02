# VerifiedDS

VerifiedDS detects data-structure and algorithm bottlenecks in C++ code, proposes optimizations using a local LLM (Ollama), and accepts changes only if proven equivalent and measurably faster.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
python tasks.py verify
```

## Running the Simulator

```powershell
python tasks.py sim
```

## Running Python Suite

```powershell
python tasks.py py
```

## Running Study Sweep

```powershell
python scripts/run_study.py --dry-run
```

## MCP Server Registration

To register the MCP server with Claude Desktop or Antigravity IDE:

```json
{
  "mcpServers": {
    "verifieds": {
      "command": "python",
      "args": ["-m", "verifieds.mcp.server"]
    }
  }
}
```

## Resource Limits & Safety Disclaimer

> [!WARNING]
> Resource limits on Windows (such as memory caps) raise `NotImplementedError` per decision D-4. The harness enforces process timeout limits but does not provide a full OS sandbox.
