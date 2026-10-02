# VerifiedDS End-to-End Execution Demo

## 1. Baseline Simulation (Set A Workload)

Gantt Schedule: `P1[0-10] P2[10-14] P3[14-16] P4[16-17]`

## 2. Static Bottleneck Detection (sim/src/ReadyQueue.hpp)

Findings Detected: 3
- [linear-min-extract] Lines 52-54: Linear min-scan comparison detected: items_ [ i ] < items_ [ best ]
- [array-queue-front-removal] Lines 56-56: Element shift detected in loop: items_ [ i ] = items_ [ i + 1 ]
- [linear-min-extract] Lines 66-68: Linear min-scan comparison detected: items_ [ i ] < items_ [ best ]

## 3. Pipeline Candidate Verification

Candidate 1 (Array -> Heap Rewrite): Equivalent=True, Speedup=2.0x
Candidate 2 (Tie-break Mutant): Equivalent=False, Reason=Output mismatch: process tie-break ordering violated

## 4. Workload Adequacy Assessment Summary

- Total Mutants Evaluated: 60
- Killed: 42
- Survived: 18
- Harness-only Adequacy Score: 0.7000
- Test-Support Mutants: 8
- Score Excluding Test-Support Lines: 0.8077
