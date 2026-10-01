# Proposed tasks (strategist only; a human promotes items into TASKS.md)

Format per item: ID (P-01...), goal, acceptance tests, deps, why it fits docs/PROJECT_BRIEF.md.

## P-01 Workload-adequacy check
- Goal: Mutate the original program and measure whether generated workload sizes distinguish mutants from the original. Flag equivalence evidence as weak when mutants remain undetected.
- Acceptance: Synthetic mutant generator produces 3 mutants (e.g. boundary offset, comparison flip). Workloads that fail to kill mutants trigger a `weak_equivalence_evidence` flag in VerifyReport.
- Dependencies: S-06 (Harness).
- Fit with brief: Strengthens the empirical verification principle ("LLM proposes, harness decides") by detecting weak workload suites.
- Literature citation: Just et al., FSE 2014 ("Are mutants a meaningful surrogate for real faults in software testing?"), URL: https://dl.acm.org/doi/10.1145/2635868.2635929

## P-02 Operation-count evidence
- Goal: Instrument dynamic execution to count basic comparisons and element moves, predict crossover size n* analytically, and validate against empirical wall-clock timing.
- Acceptance: C++ instrumentation wrapper counts comparisons/moves for Array vs Heap queues; analytical prediction matches measured n* within ±20% margin.
- Dependencies: S-01, S-06.
- Fit with brief: Provides deterministic machine-independent evidence for crossover points alongside empirical timing.
- Literature citation: Zaparanuks & Hauswirth, PLDI 2012 ("Algorithmic profiling"), URL: https://doi.org/10.1145/2254064.2254074

## P-03 Structure-choice map
- Goal: Generate a 2D matrix mapping optimal data structure selection across input sizes (10^1 to 10^6) and operation mixes (e.g. 90% read / 10% write vs 50% read / 50% write) per scheduling policy.
- Acceptance: Script outputs a structured CSV/JSON matrix comparing DynArray, MinHeap, and BST performance across 6 workload mixes.
- Dependencies: S-02, S-11.
- Fit with brief: Expands the study module (S-11) into a comprehensive empirical data structure selection map.
- Literature citation: Rice 1976 ("The Algorithm Selection Problem"), URL: https://docs.lib.purdue.edu/cstech/99

## P-04 Robustness rating across compiler configurations
- Goal: Evaluate candidate speedup across multiple optimization flags (-O0, -O2, -O3) and compilers (g++, clang++) to compute a robustness rating k/m.
- Acceptance: Pipeline reports speedup matrix across 4 compiler/flag configurations; marks candidate robust only if k/m >= 75%.
- Dependencies: S-06, S-08.
- Fit with brief: Ensures candidate speedup is not an artifact of specific compiler auto-vectorization or optimization flags.
- Literature citation: Cummins et al., CGO 2017 ("End-to-End Deep Learning of Optimization Heuristics"), URL: https://doi.org/10.1109/CGO.2017.7863738

## P-05 Peak memory footprint dimension
- Goal: Track peak memory consumption (RSS/heap allocation) per candidate and generate a Pareto time-memory trade-off report.
- Acceptance: Harness measures peak memory allocation via `getrusage`/valgrind; VerifyReport includes memory delta and highlights time vs memory trade-off choices.
- Dependencies: S-04, S-06.
- Fit with brief: Completes the empirical measurement profile beyond time complexity to include spatial complexity.
- Literature citation: Sedgewick & Wayne 2011 ("Algorithms, 4th Edition"), URL: https://algs4.cs.princeton.edu/home/
