# VerifiedDS Report Outline

## 1. Introduction & Motivation
- Project brief and automated performance verification.
- Scope and constraints: C++ scheduler simulator + Python verification tooling.

## 2. Architecture & Design
- Core simulator structures (DynArray, BST, MinHeap, ReadyQueue).
- Rule-based detector engine.
- Ollama LLM proposer integration.
- Empirical benchmark harness with crossover analysis.
- FastMCP server interface.

## 3. Safety & Verification Protocol
- Equivalence testing using seeded workloads and output hashes.
- Prompt injection protection via data block delimiters.
- Path isolation and workspace boundary checks.
- Resource limit disclaimer.

## 4. Evaluation & Results
- Multi-policy study results (FCFS, SJF, SRTF, RR, PRIORITY).
- Empirical speedup and crossover point analysis.
