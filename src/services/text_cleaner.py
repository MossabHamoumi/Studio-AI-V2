"""Text Cleaning Service.

Deterministic cleaning service that produces cleaned_text while strictly leaving
original_text immutable.
"""

import hashlib
import re
from dataclasses import dataclass


@dataclass
class CleaningResult:
    """Cleaned text payload with version and hash."""

    cleaned_text: str
    cleaning_version: str
    cleaned_hash: str


class CleaningService:
    """Deterministic text cleaner."""

    CLEANING_VERSION = "2.0"

    def clean_text(self, text: str) -> CleaningResult:
        """Clean raw text while preserving narrative content."""
        if not text:
            return CleaningResult(
                cleaned_text="",
                cleaning_version=self.CLEANING_VERSION,
                cleaned_hash=hashlib.sha256(b"").hexdigest(),
            )

        # 1. Normalize line endings and tabs
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        cleaned_lines = []
        for line in lines:
            # Strip trailing/leading spaces on lines
            stripped = line.strip()
            # Collapse multiple spaces within a line
            normalized_line = re.sub(r"[ \t]+", " ", stripped)
            cleaned_lines.append(normalized_line)

        # 2. Join lines back
        joined = "\n".join(cleaned_lines)

        # 3. Collapse more than 2 consecutive newlines to 2 newlines (preserve paragraphs)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", joined).strip()

        cleaned_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

        return CleaningResult(
            cleaned_text=cleaned_text,
            cleaning_version=self.CLEANING_VERSION,
            cleaned_hash=cleaned_hash,
        )
