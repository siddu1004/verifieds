"""Mutator module for textual C++ operator swaps (node Q4 / D-7)."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class OperatorSwap:
    """Represents a single operator swap mutation site."""

    file: str
    line: int
    column: int
    from_op: str
    to_op: str


def find_mutation_sites(filename: str, content: str) -> list[OperatorSwap]:
    """Find operator swap mutation sites in C++ source content.

    Rules (< <-> <=, > <-> >=, == <-> !=, + 1 -> + 0, - 1 -> - 0, && <-> ||),
    ordered by line and column.
    """
    sites: list[OperatorSwap] = []
    lines = content.splitlines()

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip preprocessor directives, comments, and empty lines
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("//")
            or stripped.startswith("/*")
        ):
            continue

        col = 0
        n = len(line)
        while col < n:
            # Skip string literals and comments in line
            if line[col : col + 2] == "//":
                break

            # Multi-character swaps first
            if line[col : col + 3] == "+ 1":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "+ 1", "+ 0"))
                col += 3
                continue
            elif line[col : col + 3] == "- 1":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "- 1", "- 0"))
                col += 3
                continue
            elif line[col : col + 2] == "+1" and (
                col + 2 >= n or not line[col + 2].isalnum()
            ):
                sites.append(OperatorSwap(filename, line_idx, col + 1, "+1", "+0"))
                col += 2
                continue
            elif line[col : col + 2] == "-1" and (
                col + 2 >= n or not line[col + 2].isalnum()
            ):
                # Only match -1 when used as subtrahend / value, not name or type
                sites.append(OperatorSwap(filename, line_idx, col + 1, "-1", "-0"))
                col += 2
                continue
            elif line[col : col + 2] == "&&":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "&&", "||"))
                col += 2
                continue
            elif line[col : col + 2] == "||":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "||", "&&"))
                col += 2
                continue
            elif line[col : col + 2] == "==":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "==", "!="))
                col += 2
                continue
            elif line[col : col + 2] == "!=":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "!=", "=="))
                col += 2
                continue
            elif line[col : col + 2] == "<=":
                sites.append(OperatorSwap(filename, line_idx, col + 1, "<=", "<"))
                col += 2
                continue
            elif line[col : col + 2] == ">=":
                sites.append(OperatorSwap(filename, line_idx, col + 1, ">=", ">"))
                col += 2
                continue
            elif line[col : col + 2] == "<<" or line[col : col + 2] == ">>":
                col += 2
                continue
            elif line[col] == "<":
                # Ensure it's not template <...>, include <...>, or stream <<
                sub = line[col:]
                if not re.match(r"^<[A-Za-z0-9_,\s*&:]*>", sub) and not re.match(
                    r"^<[a-z0-9_./]+>", sub
                ):
                    sites.append(OperatorSwap(filename, line_idx, col + 1, "<", "<="))
                col += 1
                continue
            elif line[col] == ">":
                sites.append(OperatorSwap(filename, line_idx, col + 1, ">", ">="))
                col += 1
                continue

            col += 1

    return sites


def apply_mutation(content: str, site: OperatorSwap) -> str:
    """Apply an OperatorSwap to content at the specified line and column."""
    lines = content.splitlines(keepends=True)
    line_idx = site.line - 1
    target_line = lines[line_idx]

    col_idx = site.column - 1
    from_len = len(site.from_op)

    # Check if target match exists at exact col_idx
    if target_line[col_idx : col_idx + from_len] == site.from_op:
        new_line = (
            target_line[:col_idx] + site.to_op + target_line[col_idx + from_len :]
        )
    else:
        # Fallback to first occurrence on line if column shifted
        new_line = target_line.replace(site.from_op, site.to_op, 1)

    lines[line_idx] = new_line
    return "".join(lines)
