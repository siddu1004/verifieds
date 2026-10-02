"""Matcher for adjacent-swap-sort rule."""

import re
from verifieds.detector.scanner import SourceView


def match(source_view: SourceView) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []

    adj_comp_pattern = re.compile(
        r"(\w+)\s*\[\s*(\w+)\s*\]\s*(?:>|<)\s*\1\s*\[\s*\2\s*\+\s*1\s*\]"
    )
    swap_pattern = re.compile(r"swap\s*\(|std::swap\s*\(")

    for outer_loop in source_view.loops:
        if outer_loop.inner_loops:
            for inner in outer_loop.inner_loops:
                body = inner.body_text
                m_comp = adj_comp_pattern.search(body)
                m_swap = (
                    swap_pattern.search(body)
                    or "=" in body  # or manual swap using temporary
                )
                if m_comp and m_swap:
                    evidence = f"Adjacent swap sorting loop detected: {m_comp.group(0)}"
                    matches.append(
                        (outer_loop.start_line, outer_loop.end_line, evidence)
                    )
                    break

    return matches
