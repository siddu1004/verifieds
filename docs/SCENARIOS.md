# VerifiedDS Scenario Catalogue

| Scenario ID | Name / Description | Purpose | Targeted Bug Class |
|---|---|---|---|
| SC-1 | Convoy | Test convoy effect handling across FCFS, SJF, SRTF, RR q=2 | Incorrect preemption or priority handling under long-burst process convoy |
| SC-2 | Simultaneous ties | Test tie-breaking for equal arrival/burst/priority processes | Indeterminate queue ordering or non-deterministic tie-breaker logic |
| SC-3 | Priority wait | Test priority queue ordering with staggered arrivals | Wait time calculation error or inverted priority insertion |
| SC-4 | Single process | Edge case with single process execution | Boundary check errors or off-by-one zero-state bugs |
| SC-5 | Late arrival (t=100) | Test idle state handling prior to first process arrival | Gantt chart gap skipping or incorrect idle time tracking |
| SC-6 | RR extremes | Test RR with q=1 and q > largest burst | Quantum calculation off-by-one or queue rotation infinite loops |
| M1 | Permutation invariance | Permuting input process order does not change output | Order-dependent state initialization bugs |
| M2 | Arrival time shift | Adding k to all arrivals shifts completion by k and leaves wait unchanged | Absolute timestamp calculation bugs |
| M3 | Workload scaling | Multiplying arrivals, bursts, quantum by 3 scales metrics by 3 | Non-linear scale bugs or unit conversion errors |
| M4 | SRTF optimality | SRTF avg waiting time <= all other policies | Inefficient preemptive scheduling logic |
| M5 | RR quantum bound | RR with quantum >= max burst equals FCFS per process | Round Robin queue rotation logic errors |
| M6 | Post-completion append | Appending process arriving after all finished leaves earlier metrics unchanged | Global state corruption across process batches |
| P-A | Correct rewrite | Accept array -> heap rewrite with speedup > 1 | False rejection of correct performance optimization |
| P-B | Tie-break mutant | Reject candidate omitting pid tie-break comparison | Output equivalence verification failure |
| P-C | Quantum off-by-one | Reject candidate with quantum off-by-one | Failure to detect subtle algorithmic state mutation |
| P-D | Fixed output candidate | Reject candidate returning fixed dummy JSON | Verification hash spoofing vulnerability |
| P-E | Late crossover | Detect crossover n* > smallest size | Timing crossover calculation error |
| P-F | Build/Loop error | Reject candidates with compile error or infinite loop | Harness deadlock or process leak on candidate crash |
| L-1 | Prose response | Handle raw prose instead of JSON from LLM | Unhandled JSON decode exception |
| L-2 | Markdown fences | Parse or reject JSON inside ```json fences | Code block extraction failure |
| L-3 | 5MB response | Handle large LLM response body gracefully | Out-of-memory or buffer overflow |
| L-4 | Extra keys | Strip or reject draft containing extra keys (e.g. id) | Schema strictness violation |
| L-5 | Empty candidates | Handle empty candidate list | Index out of bounds on empty list |
| L-6 | Slow response | Enforce timeout when LLM response is slow | Unbounded hanging on HTTP request |
| L-7 | Connection refused | Handle connection refused gracefully | Uncaught network socket crash |
| MCP-1 | In-memory session | End-to-end tool execution and schema validation | Tool output contract mismatch |
| MCP-2 | Security isolation | Block path escape attempts (.., absolute, symlinks) | Path traversal vulnerability |
