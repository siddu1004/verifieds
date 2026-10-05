"""Wiring module binding real detector, harness compiler and harness comparator."""

from pathlib import Path
from typing import Any

from verifieds.contracts import DetectFn, VerifyDiffFn
from verifieds.detector import detect_file
from verifieds.harness import compare as real_compare
from verifieds.harness import compile_program as real_compile
from verifieds.pipeline import make_verify_diff

# Export default_detect as real detector function
default_detect: DetectFn = detect_file


def build_verify_diff(
    workspace: Path | None = None,
    sizes: tuple[int, ...] | list[int] = (100, 1000, 10000),
    runs: int = 7,
    seed: int = 1234,
) -> VerifyDiffFn:
    """Build a VerifyDiffFn bound to the real compile_program and compare functions."""

    def compare_adapter(
        orig_bin: Path,
        cand_bin: Path,
        candidate_id: str,
        sizes_arg: list[int],
        runs_arg: int,
        seed_arg: int,
        workload_cmd: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return real_compare(
            orig_bin,
            cand_bin,
            candidate_id=candidate_id,
            sizes=sizes_arg,
            runs=runs_arg,
            seed=seed_arg,
            workload_cmd=workload_cmd,
            **kwargs,
        )

    return make_verify_diff(
        compile_fn=real_compile,
        compare_fn=compare_adapter,
        workspace=workspace,
        sizes=sizes,
        runs=runs,
        seed=seed,
    )
