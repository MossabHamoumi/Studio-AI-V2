"""Chapter Detection Engine.

Detects chapter boundaries, titles, Roman/Arabic numbers, sequence order, duplicates,
gaps, and front/back matter classifications.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def roman_to_int(roman: str) -> Optional[int]:
    """Convert Roman numeral string to integer."""
    roman_dict = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    roman = roman.upper().strip()
    if not roman or not all(c in roman_dict for c in roman):
        return None
    total = 0
    prev = 0
    for char in reversed(roman):
        curr = roman_dict[char]
        if curr >= prev:
            total += curr
        else:
            total -= curr
        prev = curr
    return total if total > 0 else None


WORD_TO_INT = {
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "FOUR": 4,
    "FIVE": 5,
    "SIX": 6,
    "SEVEN": 7,
    "EIGHT": 8,
    "NINE": 9,
    "TEN": 10,
    "ELEVEN": 11,
    "TWELVE": 12,
    "THIRTEEN": 13,
    "FOURTEEN": 14,
    "FIFTEEN": 15,
    "SIXTEEN": 16,
    "SEVENTEEN": 17,
    "EIGHTEEN": 18,
    "NINETEEN": 19,
    "TWENTY": 20,
}


@dataclass
class DetectedChapter:
    """Detected chapter unit."""

    chapter_number: int
    sequence_index: int
    title: str
    start_offset: int
    end_offset: int
    text: str
    classification: str = "STORY"  # FRONT_MATTER, STORY, BACK_MATTER, UNKNOWN
    metadata: Dict[str, bool] = field(default_factory=dict)


class ChapterDetector:
    """Regex & Structural Chapter Detector."""

    # Matches "Chapter 1", "CHAPTER I", "Chapter One", "CHAPTER 1.", "Book One", "Prologue", "Epilogue"
    CHAPTER_PATTERNS = [
        re.compile(r"^(CHAPTER|Chapter|BOOK|Book)\s+([0-9]+|[IVXLCDM]+|[A-Za-z]+)[\.\:]?\s*(.*)$", re.IGNORECASE),
        re.compile(r"^(PROLOGUE|Prologue|EPILOGUE|Epilogue|PREFACE|Preface|INTRODUCTION|Introduction)\b\s*(.*)$", re.IGNORECASE),
    ]

    FRONT_MATTER_TITLES = {"PROLOGUE", "PREFACE", "INTRODUCTION", "FOREWORD", "TITLE PAGE", "COPYRIGHT"}
    BACK_MATTER_TITLES = {"EPILOGUE", "AFTERWORD", "APPENDIX", "ACKNOWLEDGEMENTS", "NOTES"}

    def detect_chapters(self, text: str) -> List[DetectedChapter]:
        """Detect chapter boundaries across full text string."""
        if not text.strip():
            return []

        lines = text.splitlines(keepends=True)
        boundaries = []

        curr_offset = 0
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                curr_offset += len(line)
                continue

            match_res = self._match_chapter_heading(stripped)
            if match_res:
                c_num, title = match_res
                boundaries.append({
                    "line_idx": idx,
                    "start_offset": curr_offset,
                    "chapter_number": c_num,
                    "title": title or f"Chapter {c_num}",
                })

            curr_offset += len(line)

        # Fallback: if no chapters detected, treat whole text as Chapter 1
        if not boundaries:
            return [
                DetectedChapter(
                    chapter_number=1,
                    sequence_index=0,
                    title="Chapter 1",
                    start_offset=0,
                    end_offset=len(text),
                    text=text,
                    classification="STORY",
                )
            ]

        # Handle front matter if first chapter starts after offset 0
        chapters: List[DetectedChapter] = []
        seq_idx = 0

        if boundaries[0]["start_offset"] > 0:
            fm_text = text[0:boundaries[0]["start_offset"]]
            if fm_text.strip():
                chapters.append(
                    DetectedChapter(
                        chapter_number=0,
                        sequence_index=seq_idx,
                        title="Front Matter",
                        start_offset=0,
                        end_offset=boundaries[0]["start_offset"],
                        text=fm_text,
                        classification="FRONT_MATTER",
                    )
                )
                seq_idx += 1

        # Construct chapter objects with text spans
        seen_numbers = set()
        prev_cnum: Optional[int] = None

        for idx, b in enumerate(boundaries):
            start = b["start_offset"]
            end = boundaries[idx + 1]["start_offset"] if idx + 1 < len(boundaries) else len(text)
            c_text = text[start:end]
            c_num = b["chapter_number"]
            title = b["title"]

            # Classify chapter
            upper_title = title.upper()
            classification = "STORY"
            if any(fm in upper_title for fm in self.FRONT_MATTER_TITLES):
                classification = "FRONT_MATTER"
            elif any(bm in upper_title for bm in self.BACK_MATTER_TITLES):
                classification = "BACK_MATTER"

            metadata: Dict[str, bool] = {}

            # Duplicate detection
            if c_num in seen_numbers and c_num != 0:
                metadata["DUPLICATE_SUSPECTED"] = True
            seen_numbers.add(c_num)

            # Gap detection
            if prev_cnum is not None and c_num > prev_cnum + 1 and c_num != 0 and prev_cnum != 0:
                metadata["GAP_AFTER_PREVIOUS"] = True

            prev_cnum = c_num

            chapters.append(
                DetectedChapter(
                    chapter_number=c_num,
                    sequence_index=seq_idx,
                    title=title,
                    start_offset=start,
                    end_offset=end,
                    text=c_text,
                    classification=classification,
                    metadata=metadata,
                )
            )
            seq_idx += 1

        return chapters

    def _match_chapter_heading(self, line: str) -> Optional[Tuple[int, str]]:
        """Match heading pattern and extract chapter number and title."""
        # 1. Prologue / Epilogue
        m_special = self.CHAPTER_PATTERNS[1].match(line)
        if m_special:
            heading = m_special.group(1).capitalize()
            subtitle = m_special.group(2).strip()
            title = f"{heading} - {subtitle}" if subtitle else heading
            return 0, title

        # 2. Chapter X / Book X
        m_chap = self.CHAPTER_PATTERNS[0].match(line)
        if m_chap:
            num_str = m_chap.group(2).strip().upper()
            subtitle = m_chap.group(3).strip()

            c_num = 1
            if num_str.isdigit():
                c_num = int(num_str)
            elif num_str in WORD_TO_INT:
                c_num = WORD_TO_INT[num_str]
            else:
                r_num = roman_to_int(num_str)
                if r_num:
                    c_num = r_num

            prefix = m_chap.group(1).capitalize()
            title = f"{prefix} {num_str}"
            if subtitle:
                title = f"{title}: {subtitle}"

            return c_num, title

        return None
