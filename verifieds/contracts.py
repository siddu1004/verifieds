"""Interfaces between parallel lanes. Real code and test fakes both satisfy them."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from verifieds.schemas.models import CandidateDraft, Finding, VerifyReport


class Proposer(Protocol):
    def propose(self, finding: Finding, code_snippet: str) -> list[CandidateDraft]: ...


# (source_file) -> findings
DetectFn = Callable[[Path], list[Finding]]

# (source_dir, main_file, output_path) -> built program path
CompileFn = Callable[[Path, str, Path], Path]

# (original_binary, candidate_binary, candidate_id, sizes, runs, seed) -> report
CompareFn = Callable[[Path, Path, str, Sequence[int], int, int], VerifyReport]

# (source_dir, main_file, unified_diff, candidate_id) -> report
VerifyDiffFn = Callable[[Path, str, str, str], VerifyReport]
