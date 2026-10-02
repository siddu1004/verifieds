"""Pydantic models for CandidateDraft, Finding, Candidate, and VerifyReport schemas."""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CandidateDraft(BaseModel):
    """Raw candidate modification proposed directly by the LLM (without system IDs)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: str
    diff: str
    expected_complexity_after: str
    risks: list[str]


class Finding(BaseModel):
    """Suboptimal data structure or algorithm finding in analysed C++ code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    rule_id: str
    file: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    adt: Literal["queue", "stack", "priority_queue", "list", "sort", "search"]
    impl: str
    complexity_before: str
    evidence: str

    @model_validator(mode="after")
    def validate_line_numbers(self) -> "Finding":
        """Validate start_line <= end_line."""
        if self.start_line > self.end_line:
            raise ValueError(
                f"start_line ({self.start_line}) must be <= end_line ({self.end_line})"
            )
        return self


class Candidate(BaseModel):
    """Proposed candidate created by the pipeline from a Finding and CandidateDraft."""

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

    n: int = Field(gt=0)
    original_ms_median: float = Field(ge=0.0)
    candidate_ms_median: float = Field(ge=0.0)
    runs: int = Field(gt=0)


class VerifyReport(BaseModel):
    """Verification and benchmarking report for a proposed candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    equivalent: bool
    rejected_reason: str | None = None
    workloads: list[WorkloadResult]
    speedup_at_max_n: float | None = Field(default=None, gt=0.0)
    crossover_n: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_equivalence_rules(self) -> "VerifyReport":
        """Validate rejected_reason, speedup_at_max_n, and workloads per D-1."""
        if not self.equivalent:
            if not self.rejected_reason:
                raise ValueError("rejected_reason is required when equivalent is False")
            if self.speedup_at_max_n is not None:
                raise ValueError(
                    "speedup_at_max_n must be None when equivalent is False"
                )
        else:
            if self.rejected_reason is not None:
                raise ValueError("rejected_reason must be None when equivalent is True")
            if self.speedup_at_max_n is None:
                raise ValueError("speedup_at_max_n is required when equivalent is True")
            if not self.workloads:
                raise ValueError("workloads cannot be empty when equivalent is True")
        return self

    def __getitem__(self, item: str) -> Any:
        if item == "reason":
            return self.rejected_reason
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        if item == "reason":
            return self.rejected_reason if self.rejected_reason is not None else default
        return getattr(self, item, default)


class MutantResult(BaseModel):
    """Result for a single mutation site test."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    file: str
    line: int = Field(ge=1)
    from_op: str = Field(alias="from")
    to_op: str = Field(alias="to")
    status: Literal["killed", "survived", "invalid"]


class AdequacyReport(BaseModel):
    """Workload adequacy score and mutation testing report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mutants: list[MutantResult]
    killed: int = Field(ge=0)
    survived: int = Field(ge=0)
    invalid: int = Field(ge=0)
    score: float = Field(ge=0.0, le=1.0)
    test_support_count: int = Field(default=0, ge=0)
    score_excluding_test_support: float = Field(default=0.0, ge=0.0, le=1.0)
