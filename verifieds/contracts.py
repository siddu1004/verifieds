"""Interfaces between parallel lanes. Real code and test fakes both satisfy them."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from verifieds.schemas.models import CandidateDraft, Finding, VerifyReport


class Proposer(Protocol):
    def propose(self, finding: Finding, code_snippet: str) -> list[CandidateDraft]: ...


# (source_file) -> findings
DetectFn = Callable[[Path], list[Finding]]

# (source_dir, main_file, output_path) -> built program path
CompileFn = Callable[[Path, str, Path], Path]


class CompareFn(Protocol):
    def __call__(
        self,
        original: Path,
        candidate: Path,
        candidate_id: str,
        sizes: Sequence[int],
        runs: int,
        seed: int,
        workload_cmd: str | None = None,
        **kwargs: Any,
    ) -> VerifyReport: ...


class VerifyDiffFn(Protocol):
    def __call__(
        self,
        source_dir: Path,
        main_file: str,
        diff: str,
        candidate_id: str,
        workload_cmd: str | None = None,
    ) -> VerifyReport: ...
