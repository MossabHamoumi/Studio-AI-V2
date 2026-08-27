"""Section Splitter Service.

Splits chapter text into structural paragraph sections, dialogue turns, and phone call roles.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List
from src.domain.models import SectionType


@dataclass
class ParsedSection:
    """Parsed section metadata and text."""

    sequence_index: int
    section_type: SectionType
    text: str
    start_offset: int
    end_offset: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class SectionSplitter:
    """Splits chapter text into structural sections."""

    DIALOGUE_REGEX = re.compile(r'["“«]([^"”»]+)["”»]')
    SPEAKER_ROLE_REGEX = re.compile(r"^([A-Z][A-Za-z0-9_\s]{1,20})\s*:\s*(.*)$")

    def split_chapter_to_sections(self, chapter_text: str) -> List[ParsedSection]:
        """Split chapter text into paragraph and dialogue sections."""
        if not chapter_text.strip():
            return []

        paragraphs = chapter_text.split("\n\n")
        sections: List[ParsedSection] = []

        curr_offset = 0
        seq_idx = 0

        for p in paragraphs:
            p_len = len(p)
            stripped = p.strip()

            if not stripped:
                curr_offset += p_len + 2  # account for \n\n
                continue

            sec_type = SectionType.NARRATION
            metadata: Dict[str, Any] = {}

            # Check Phone Call / Script Dialogue Speaker pattern "SPEAKER: text"
            speaker_match = self.SPEAKER_ROLE_REGEX.match(stripped)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                dialogue_body = speaker_match.group(2).strip()
                sec_type = SectionType.DIALOGUE
                metadata = {
                    "speaker": speaker,
                    "role": "SPEAKER",
                    "dialogue": dialogue_body,
                }
                # Check for sound cue like "[Ringing]"
                if dialogue_body.startswith("[") and dialogue_body.endswith("]"):
                    metadata["role"] = "SOUND_CUE"
            elif self.DIALOGUE_REGEX.search(stripped):
                sec_type = SectionType.DIALOGUE
                quotes = self.DIALOGUE_REGEX.findall(stripped)
                metadata["quotes"] = quotes

            sections.append(
                ParsedSection(
                    sequence_index=seq_idx,
                    section_type=sec_type,
                    text=stripped,
                    start_offset=curr_offset,
                    end_offset=curr_offset + len(stripped),
                    metadata=metadata,
                )
            )

            seq_idx += 1
            curr_offset += p_len + 2

        return sections
