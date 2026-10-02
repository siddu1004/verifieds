# VerifiedDS Claims Audit

The table below maps every claim in `README.md` and `docs/REPORT_OUTLINE.md` to the exact unit or scenario test function that proves it.

| Source | Claim Text | Test Function |
|---|---|---|
| README.md | VerifiedDS detects data-structure and algorithm bottlenecks in C++ code | `tests/test_detector.py::test_rule_fixtures` |
| README.md | proposes optimizations using a local LLM (Ollama) | `tests/test_proposer.py::test_proposer_valid_response` |
| README.md | accepts changes only if proven equivalent and measurably faster | `tests/test_pipeline.py::test_pipeline_accepted_rewrite` |
| README.md | Resource limits on Windows (such as memory caps) raise NotImplementedError per decision D-4 | `tests/test_harness.py::test_set_memory_limit_windows` |
| README.md | The harness enforces process timeout limits but does not provide a full OS sandbox | `tests/test_harness.py::test_harness_runaway_timeout` |
| docs/REPORT_OUTLINE.md | Core simulator structures (DynArray, BST, MinHeap, ReadyQueue) | `tests/test_smoke.py::test_package_importable` |
| docs/REPORT_OUTLINE.md | Rule-based detector engine | `tests/test_detector.py::test_rule_loader` |
| docs/REPORT_OUTLINE.md | Ollama LLM proposer integration | `tests/test_proposer.py::test_proposer_valid_response` |
| docs/REPORT_OUTLINE.md | Empirical benchmark harness with crossover analysis | `tests/test_harness.py::test_harness_synthetic_on_vs_on2` |
| docs/REPORT_OUTLINE.md | FastMCP server interface | `tests/test_mcp.py::test_mcp_tools_in_process` |
| docs/REPORT_OUTLINE.md | Equivalence testing using seeded workloads and output hashes | `tests/test_harness.py::test_harness_with_sim_cli` |
| docs/REPORT_OUTLINE.md | Prompt injection protection via data block delimiters | `tests/test_safety.py::test_prompt_injection_ignored` |
| docs/REPORT_OUTLINE.md | Path isolation and workspace boundary checks | `tests/test_safety.py::test_harness_workspace_isolation` |
| docs/REPORT_OUTLINE.md | Resource limit disclaimer | `tests/test_safety.py::test_env_secrets_not_leaked` |
| docs/REPORT_OUTLINE.md | Multi-policy study results (FCFS, SJF, SRTF, RR, PRIORITY) | `tests/test_scenarios_sim.py::test_hand_computed_scenarios` |
| docs/REPORT_OUTLINE.md | Empirical speedup and crossover point analysis | `tests/test_scenarios_pipeline.py::test_pe_late_crossover` |
