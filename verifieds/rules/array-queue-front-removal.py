"""Matcher for array-queue-front-removal rule."""

import re

from verifieds.detector.scanner import SourceView

SHIFT_PATTERN = re.compile(r"(\w+)\s*\[\s*(\w+)\s*\]\s*=\s*\1\s*\[\s*\2\s*\+\s*1\s*\]")
ERASE_PATTERN = re.compile(r"\.?\s*erase\s*\(\s*\w+\s*\.\s*begin\s*\(")


def _is_swap(body: str, name: str, index: str) -> bool:
    """True when the loop also writes back to name[index + 1].

    A left shift only ever writes to name[index]; a swap writes to both
    halves, so name[index + 1] = ... means this is an exchange (bubble
    sort), not a dequeue.
    """
    write_back = re.compile(
        rf"{re.escape(name)}\s*\[\s*{re.escape(index)}\s*\+\s*1\s*\]\s*=(?!=)"
    )
    return write_back.search(body) is not None


def match(source_view: SourceView) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []

    for loop in source_view.loops:
        body = loop.body_text
        m_shift = SHIFT_PATTERN.search(body)
        m_erase = ERASE_PATTERN.search(body)

        if m_shift and not _is_swap(body, m_shift.group(1), m_shift.group(2)):
            evidence = f"Element shift detected in loop: {m_shift.group(0)}"
            matches.append((loop.start_line, loop.end_line, evidence))
        elif m_erase:
            evidence = f"Front erase detected in loop: {m_erase.group(0)}"
            matches.append((loop.start_line, loop.end_line, evidence))

    return matches
