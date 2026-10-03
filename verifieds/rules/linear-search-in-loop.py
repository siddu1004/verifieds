"""Matcher for linear-search-in-loop rule."""

import re
from verifieds.detector.scanner import SourceView


def match(source_view: SourceView) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []

    eq_comp_pattern = re.compile(r"(\w+)\s*\[\s*(\w+)\s*\]\s*==\s*(\w+)")

    for outer_loop in source_view.loops:
        if outer_loop.inner_loops:
            for inner in outer_loop.inner_loops:
                body = inner.body_text
                m_comp = eq_comp_pattern.search(body)
                has_exit = "return" in body or "break" in body
                if m_comp and has_exit:
                    evidence = f"Linear search in loop detected: {m_comp.group(0)}"
                    matches.append(
                        (outer_loop.start_line, outer_loop.end_line, evidence)
                    )
                    break

    return matches
