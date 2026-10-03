# VerifiedDS End-to-End Execution Demo

## 1. Baseline Simulation (Set A Workload)

Gantt Schedule: `P1[0-8] P2[8-12] P3[12-21] P4[21-26]`

## 2. Static Bottleneck Detection (sim/src/ReadyQueue.hpp)

Findings Detected: 3
- [linear-min-extract] Lines 52-54: Linear min-scan comparison detected: items_ [ i ] < items_ [ best ]
- [array-queue-front-removal] Lines 56-56: Element shift detected in loop: items_ [ i ] = items_ [ i + 1 ]
- [linear-min-extract] Lines 66-68: Linear min-scan comparison detected: items_ [ i ] < items_ [ best ]

## 3. Pipeline Candidate Verification

Candidate 1 (Array -> Heap Config Rewrite): Equivalent=True
Candidate 2 (Tie-break Mutant): Equivalent=False, Reason=Output mismatch at n=20

## 4. Workload Adequacy Assessment Summary

- Total Mutants Evaluated: 60
- Killed: 47
- Survived: 13
- Harness-only Adequacy Score: 0.7833
- Test-Support Mutants: 7
- Score Excluding Test-Support Lines: 0.8868
