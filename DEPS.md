# Dependencies
# Format: package | pinned version | why it is needed

pydantic       | >=2.7   | Single source of truth for Finding, Candidate, VerifyReport data shapes (S-04)
ruff           | >=0.4   | Linter: rules F E B ARG UP SIM (quality gate)
mypy           | >=1.10  | Static type checker, --strict (quality gate)
vulture        | >=2.11  | Dead-code detector (quality gate)
pytest         | >=8.2   | Test runner (quality gate)
pytest-cov     | >=5.0   | Branch coverage enforcement ≥ 90 % (quality gate)
