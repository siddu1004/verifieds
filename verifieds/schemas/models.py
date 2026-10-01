"""Pydantic models for Finding, Candidate, and VerifyReport schemas."""

from typing import Literal
from pydantic import BaseModel, ConfigDict


class Finding(BaseModel):
    """Suboptimal data structure or algorithm finding in analysed C++ code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    rule_id: str
    file: str
    start_line: int
    end_line: int
    adt: Literal["queue", "stack", "priority_queue", "list", "sort", "search"]
    impl: str
    complexity_before: str
    evidence: str


class Candidate(BaseModel):
    """Proposed data structure or algorithm modification candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    finding_id: str
    strategy: str
    diff: str
    expected_complexity_after: str
    risks: list[str]


class WorkloadResult(BaseModel):
    """Performance measurement result for a single workload size n."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    n: int
    original_ms_median: float
    candidate_ms_median: float
    runs: int


class VerifyReport(BaseModel):
    """Verification and benchmarking report for a proposed candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    equivalent: bool
    rejected_reason: str | None = None
    workloads: list[WorkloadResult]
    speedup_at_max_n: float
    crossover_n: int | None = None
