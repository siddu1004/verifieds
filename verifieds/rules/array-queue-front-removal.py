"""Matcher for array-queue-front-removal rule."""

import re
from verifieds.detector.scanner import SourceView


def match(source_view: SourceView) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []

    shift_pattern = re.compile(
        r"(\w+)\s*\[\s*(\w+)\s*\]\s*=\s*\1\s*\[\s*\2\s*\+\s*1\s*\]"
    )
    erase_pattern = re.compile(r"\.erase\s*\(\s*\w+\.begin\s*\(\s*\)")

    for loop in source_view.loops:
        body = loop.body_text
        m_shift = shift_pattern.search(body)
        m_erase = erase_pattern.search(body)

        if m_shift:
            evidence = f"Element shift detected in loop: {m_shift.group(0)}"
            matches.append((loop.start_line, loop.end_line, evidence))
        elif m_erase:
            evidence = f"Front erase detected in loop: {m_erase.group(0)}"
            matches.append((loop.start_line, loop.end_line, evidence))

    return matches
