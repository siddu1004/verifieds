verify: verify-sim verify-py

verify-sim:
	cmake -S sim -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
	cmake --build build
	ctest --test-dir build --output-on-failure
	cppcheck --enable=warning,style,unusedFunction --std=c++20 --error-exitcode=1 --inline-suppr -I sim/src --suppress=missingIncludeSystem sim/src/*.hpp sim/tests/*.cpp

verify-py:
	python -m ruff check .
	python -m ruff format --check .
	python -m mypy --strict verifieds
	python -m vulture verifieds --min-confidence 80
	python -m verifieds.schemas.export --check
	python -m pytest --cov=verifieds --cov-branch --cov-fail-under=90

tools-check:
	cmake --version    || echo "MISSING: cmake"
	g++ --version      || echo "MISSING: g++"
	cppcheck --version || echo "MISSING: cppcheck"
	python --version
	python -m ruff --version
	python -m mypy --version
	python -m vulture --version
	python -m pytest --version
	ollama --version   || echo "MISSING: ollama"

.PHONY: verify verify-sim verify-py tools-check
