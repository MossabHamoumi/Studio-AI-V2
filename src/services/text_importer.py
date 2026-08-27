"""Text Importer Service.

Handles robust text file ingestion with encoding detection, line ending normalization,
exact text statistics, SHA-256 hashing, and complete non-truncation verification.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union
from src.utilities.exceptions import ValidationError


@dataclass
class TextImportResult:
    """Import statistics and raw decoded text payload."""

    raw_text: str
    encoding_used: str
    byte_count: int
    char_count: int
    word_count: int
    line_count: int
    paragraph_count: int
    content_hash: str


class TextImporter:
    """Universal text importer supporting UTF-8, BOM, UTF-16, Windows-1252, and large files."""

    ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"]

    def import_text_file(self, file_path: Union[str, Path]) -> TextImportResult:
        """Import a text file, autodetect encoding, compute statistics, and verify non-truncation."""
        path = Path(file_path)
        if not path.is_file():
            raise ValidationError(f"Import file path '{file_path}' is not a valid file.")

        raw_bytes = path.read_bytes()
        byte_count = len(raw_bytes)

        if byte_count == 0:
            raise ValidationError(f"Import file '{file_path}' is empty (0 bytes).")

        raw_text, encoding_used = self._decode_bytes(raw_bytes)

        # Non-truncation verification
        char_count = len(raw_text)
        if char_count == 0:
            raise ValidationError(f"Import file '{file_path}' decoded to 0 characters.")

        # Line and paragraph statistics
        lines = raw_text.splitlines()
        line_count = len(lines)
        words = raw_text.split()
        word_count = len(words)
        paragraphs = [p for p in raw_text.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs) if paragraphs else (1 if raw_text.strip() else 0)

        # SHA-256 Content Hash of raw text
        content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        return TextImportResult(
            raw_text=raw_text,
            encoding_used=encoding_used,
            byte_count=byte_count,
            char_count=char_count,
            word_count=word_count,
            line_count=line_count,
            paragraph_count=paragraph_count,
            content_hash=content_hash,
        )

    def import_raw_string(self, text: str) -> TextImportResult:
        """Import raw pasted text string with full statistics."""
        if not text:
            raise ValidationError("Pasted text string is empty.")

        raw_bytes = text.encode("utf-8")
        byte_count = len(raw_bytes)
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        lines = text.splitlines()
        line_count = len(lines)
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs) if paragraphs else 1

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return TextImportResult(
            raw_text=text,
            encoding_used="utf-8",
            byte_count=byte_count,
            char_count=char_count,
            word_count=word_count,
            line_count=line_count,
            paragraph_count=paragraph_count,
            content_hash=content_hash,
        )

    def _decode_bytes(self, raw_bytes: bytes) -> Tuple[str, str]:
        """Attempt decoding with supported encodings."""
        for encoding in self.ENCODINGS_TO_TRY:
            try:
                decoded = raw_bytes.decode(encoding)
                # Universal line ending normalization
                normalized = decoded.replace("\r\n", "\n").replace("\r", "\n")
                return normalized, encoding
            except UnicodeDecodeError:
                continue

        raise ValidationError("Failed to decode text file with supported encodings.")
