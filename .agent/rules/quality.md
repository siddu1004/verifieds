# Quality gates (apply to every change)
- C++20: -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror; ASan and UBSan in tests; cppcheck unusedFunction clean.
- Python >= 3.11: ruff (rules F, E, B, ARG, UP, SIM), mypy --strict, vulture --min-confidence 80, pytest --cov-branch --cov-fail-under=90.
- Every function has a test that would fail if the function were deleted.
- Every detector rule has one positive and one negative fixture under tests/fixtures/.
- Public data shapes come from schemas/*.json, generated from the Pydantic models; never hand-edit them.
- Determinism: seeded randomness only; no wall-clock values in asserted output.
- Third-party code is used only through documented, installed APIs.
