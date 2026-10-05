"""Pure-Python C++ token scanner for pattern detection (Decision D-3)."""

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    col: int


@dataclass
class LoopBlock:
    kind: str  # "for" or "while"
    start_line: int
    end_line: int
    header_text: str
    body_text: str
    tokens: list[Token] = field(default_factory=list)
    inner_loops: list["LoopBlock"] = field(default_factory=list)


class SourceView:
    """Cleaned source code view with comments/strings stripped and loops indexed."""

    def __init__(self, raw_code: str):
        self.raw_code = raw_code
        self.clean_code = self._strip_comments_and_strings(raw_code)
        self.lines = self.clean_code.splitlines()
        self.tokens = self._tokenize(self.clean_code)
        self.loops = self._extract_loops()

    @staticmethod
    def _strip_comments_and_strings(code: str) -> str:
        """Strip comments and string literals, preserving line numbers."""
        chars = list(code)
        n = len(chars)
        i = 0
        in_line_comment = False
        in_block_comment = False
        in_string = False
        string_char = ""

        while i < n:
            c = chars[i]
            nxt = chars[i + 1] if i + 1 < n else ""

            if in_line_comment:
                if c == "\n":
                    in_line_comment = False
                else:
                    chars[i] = " "
                i += 1
                continue

            if in_block_comment:
                if c == "*" and nxt == "/":
                    chars[i] = " "
                    chars[i + 1] = " "
                    in_block_comment = False
                    i += 2
                else:
                    if c != "\n":
                        chars[i] = " "
                    i += 1
                continue

            if in_string:
                if c == "\\" and i + 1 < n:
                    if chars[i] != "\n":
                        chars[i] = " "
                    if chars[i + 1] != "\n":
                        chars[i + 1] = " "
                    i += 2
                    continue
                if c == string_char:
                    chars[i] = " "
                    in_string = False
                else:
                    if c != "\n":
                        chars[i] = " "
                i += 1
                continue

            # Check start of comment or string
            if c == "/" and nxt == "/":
                chars[i] = " "
                chars[i + 1] = " "
                in_line_comment = True
                i += 2
            elif c == "/" and nxt == "*":
                chars[i] = " "
                chars[i + 1] = " "
                in_block_comment = True
                i += 2
            elif c in ('"', "'"):
                chars[i] = " "
                in_string = True
                string_char = c
                i += 1
            else:
                i += 1

        return "".join(chars)

    @staticmethod
    def _tokenize(code: str) -> list[Token]:
        """Tokenize C++ code keeping track of line and column numbers."""
        token_pattern = re.compile(
            r"[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|\+\+|--|&&|\|\||::|->|<<|>>|[{}()\[\];,.<>+=\-*/%&|^~!?:#]"
        )
        tokens: list[Token] = []
        for line_num, line_str in enumerate(code.splitlines(), start=1):
            for match in token_pattern.finditer(line_str):
                tokens.append(
                    Token(text=match.group(0), line=line_num, col=match.start() + 1)
                )
        return tokens

    def _find_statement_end(self, start_idx: int) -> int:
        n = len(self.tokens)
        if start_idx >= n:
            return n - 1
        tok = self.tokens[start_idx]
        if tok.text == "{":
            depth = 0
            for j in range(start_idx, n):
                if self.tokens[j].text == "{":
                    depth += 1
                elif self.tokens[j].text == "}":
                    depth -= 1
                    if depth == 0:
                        return j
            return n - 1
        if tok.text in ("for", "while"):
            h_depth = 0
            h_end = -1
            for j in range(start_idx + 1, n):
                if self.tokens[j].text == "(":
                    h_depth += 1
                elif self.tokens[j].text == ")":
                    h_depth -= 1
                    if h_depth == 0:
                        h_end = j
                        break
            if h_end != -1 and h_end + 1 < n:
                return self._find_statement_end(h_end + 1)
            return n - 1
        if tok.text == "if":
            h_depth = 0
            h_end = -1
            for j in range(start_idx + 1, n):
                if self.tokens[j].text == "(":
                    h_depth += 1
                elif self.tokens[j].text == ")":
                    h_depth -= 1
                    if h_depth == 0:
                        h_end = j
                        break
            if h_end != -1 and h_end + 1 < n:
                then_end = self._find_statement_end(h_end + 1)
                if then_end + 1 < n and self.tokens[then_end + 1].text == "else":
                    return self._find_statement_end(then_end + 2)
                return then_end
            return n - 1

        p_depth = 0
        b_depth = 0
        for j in range(start_idx, n):
            t = self.tokens[j].text
            if t in ("(", "["):
                p_depth += 1
            elif t in (")", "]"):
                p_depth = max(0, p_depth - 1)
            elif t == "{":
                b_depth += 1
            elif t == "}":
                b_depth = max(0, b_depth - 1)
            elif t == ";" and p_depth == 0 and b_depth == 0:
                return j
        return n - 1

    def _extract_loops(self) -> list[LoopBlock]:
        """Extract loop blocks with brace or single-statement body matching."""
        loops: list[LoopBlock] = []
        n = len(self.tokens)

        for i in range(n):
            tok = self.tokens[i]
            if (
                tok.text in ("for", "while")
                and i + 1 < n
                and self.tokens[i + 1].text == "("
            ):
                # Header starts at tok, check if followed by '('

                # Find closing ')' of loop header
                depth = 0
                header_end = -1
                for j in range(i + 1, n):
                    if self.tokens[j].text == "(":
                        depth += 1
                    elif self.tokens[j].text == ")":
                        depth -= 1
                        if depth == 0:
                            header_end = j
                            break
                if header_end == -1:
                    continue

                header_tokens = self.tokens[i : header_end + 1]
                header_text = " ".join(t.text for t in header_tokens)

                # Determine body
                body_start = header_end + 1
                if body_start >= n:
                    continue

                start_line = tok.line
                body_end = self._find_statement_end(body_start)
                body_tokens = self.tokens[body_start : body_end + 1]
                end_line = (
                    body_tokens[-1].line
                    if body_tokens
                    else self.tokens[header_end].line
                )

                body_text = " ".join(t.text for t in body_tokens)
                loops.append(
                    LoopBlock(
                        kind=tok.text,
                        start_line=start_line,
                        end_line=end_line,
                        header_text=header_text,
                        body_text=body_text,
                        tokens=self.tokens[i : body_end + 1],
                    )
                )

        # Build inner loops relationship
        for loop in loops:
            for child in loops:
                if (
                    loop != child
                    and loop.start_line <= child.start_line
                    and loop.end_line >= child.end_line
                ):
                    loop.inner_loops.append(child)

        return loops
