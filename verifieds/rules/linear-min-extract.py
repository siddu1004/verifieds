"""Matcher for linear-min-extract rule."""

import re
from verifieds.detector.scanner import SourceView


def match(source_view: SourceView) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []

    # Pattern: X[i] < X[best] or X[best] > X[i]
    comp_pattern1 = re.compile(r"(\w+)\s*\[\s*(\w+)\s*\]\s*<\s*\1\s*\[\s*(\w+)\s*\]")
    comp_pattern2 = re.compile(r"(\w+)\s*\[\s*(\w+)\s*\]\s*>\s*\1\s*\[\s*(\w+)\s*\]")

    for loop in source_view.loops:
        header = loop.header_text
        body = loop.body_text

        # Extract loop iterator variable from for/while header or body
        # (e.g. for (int i = ...; ...; ++i))

        iter_match = re.search(r"for\s*\(\s*(?:[\w:\s]+\s+)?(\w+)\s*=", header)
        if not iter_match:
            iter_match = re.search(r"while\s*\(\s*(\w+)", header)
        loop_var = iter_match.group(1) if iter_match else None

        m1 = comp_pattern1.search(body)
        m2 = comp_pattern2.search(body)

        if m1:
            idx1, idx2 = m1.group(2), m1.group(3)
            # One of idx1 or idx2 should be loop_var, and the other best_var
            best_var = None
            if loop_var and idx1 == loop_var:
                best_var = idx2
            elif loop_var and idx2 == loop_var:
                best_var = idx1

            if best_var and loop_var:
                # Check for assignment best_var = loop_var
                assign_pattern = re.compile(
                    rf"\b{re.escape(str(best_var))}\s*=\s*{re.escape(str(loop_var))}\b"
                )
                if assign_pattern.search(body):
                    evidence = f"Linear min-scan comparison detected: {m1.group(0)}"
                    matches.append((loop.start_line, loop.end_line, evidence))

        elif m2:
            idx1, idx2 = m2.group(2), m2.group(3)
            best_var = None
            if loop_var and idx2 == loop_var:
                best_var = idx1
            elif loop_var and idx1 == loop_var:
                best_var = idx2

            if best_var and loop_var:
                assign_pattern = re.compile(
                    rf"\b{re.escape(str(best_var))}\s*=\s*{re.escape(str(loop_var))}\b"
                )
                if assign_pattern.search(body):
                    evidence = f"Linear min-scan comparison detected: {m2.group(0)}"
                    matches.append((loop.start_line, loop.end_line, evidence))

    return matches
