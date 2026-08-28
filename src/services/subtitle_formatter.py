"""Subtitle Text Formatter, Line Wrapper, and Metadata Filter."""

import re
from typing import List


class SubtitleFormatter:
    """Handles word-boundary line wrapping, metadata filtering, and Roman numeral speech normalization."""

    GUTENBERG_PATTERNS = [
        re.compile(r"^\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG.*", re.IGNORECASE),
        re.compile(r"^\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG.*", re.IGNORECASE),
        re.compile(r"^Project Gutenberg eBook of.*", re.IGNORECASE),
        re.compile(r"^Transcribed from.*by.*", re.IGNORECASE),
    ]

    ROMAN_NUMERAL_PATTERN = re.compile(
        r"\b(Chapter|CHAPTER|Part|PART|Book|BOOK)\s+([IVXLCDM]+)\b"
    )

    ROMAN_DICT = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

    def wrap_text(self, text: str, max_line_len: int = 36, max_lines: int = 2) -> str:
        """Wrap text cleanly on word boundaries respecting max line length and lines."""
        if not text or len(text) <= max_line_len:
            return text.strip()

        words = text.split()
        lines: List[str] = []
        curr_line: List[str] = []
        curr_len = 0

        for w in words:
            if curr_len + len(w) + (1 if curr_line else 0) <= max_line_len:
                curr_line.append(w)
                curr_len += len(w) + (1 if len(curr_line) > 1 else 0)
            else:
                if curr_line:
                    lines.append(" ".join(curr_line))
                curr_line = [w]
                curr_len = len(w)

        if curr_line:
            lines.append(" ".join(curr_line))

        # Respect max lines limit
        if len(lines) > max_lines:
            # Group extra lines onto last visible line
            top_lines = lines[: max_lines - 1]
            bottom_text = " ".join(lines[max_lines - 1 :])
            top_lines.append(bottom_text)
            return "\n".join(top_lines)

        return "\n".join(lines)

    def normalize_roman_numerals(self, text: str) -> str:
        """Narration-only normalization converting Roman numerals in titles to Arabic numbers."""

        def _replace_roman(match: re.Match) -> str:
            prefix = match.group(1)
            roman_str = match.group(2).upper()
            total = 0
            prev = 0
            for char in reversed(roman_str):
                curr = self.ROMAN_DICT.get(char, 0)
                if curr >= prev:
                    total += curr
                else:
                    total -= curr
                prev = curr
            return f"{prefix} {total}" if total > 0 else match.group(0)

        return self.ROMAN_NUMERAL_PATTERN.sub(_replace_roman, text)

    def filter_gutenberg_metadata(self, text: str) -> str:
        """Filter out Project Gutenberg metadata boilerplate lines."""
        lines = text.splitlines()
        filtered = []
        for line in lines:
            if not any(pattern.match(line.strip()) for pattern in self.GUTENBERG_PATTERNS):
                filtered.append(line)
        return "\n".join(filtered)
