# Dependencies
# Format: package | pinned version | why it is needed

pydantic   | ==2.13.4 | Single source of truth for Finding, Candidate, VerifyReport data shapes (S-04)
mcp        | ==1.30.0 | Official Python MCP SDK for stdio MCP server tools (S-09)

ruff       | ==0.16.9 | Linter: rules F E B ARG UP SIM (quality gate)

mypy       | ==2.3.1  | Static type checker, --strict (quality gate)
vulture    | ==2.16   | Dead-code detector (quality gate)
pytest     | ==9.1.1  | Test runner (quality gate)
pytest-cov | ==7.1.0  | Branch coverage enforcement ≥ 90 % (quality gate)

## Runtime Requirements (Non-pip)
- Ollama (standalone service): HTTP server running locally on `http://localhost:11434` for candidate generation (S-07).
