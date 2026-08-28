"""Subtitle Domain Models and Style Profiles."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SubtitleFormat(str, Enum):
    ASS = "ASS"
    SRT = "SRT"


class SubtitleStyleProfile(str, Enum):
    DEFAULT = "DEFAULT"
    YOUTUBE = "YOUTUBE"
    SHORT_FORM = "SHORT_FORM"
    MOBILE_LARGE = "MOBILE_LARGE"
    CINEMATIC = "CINEMATIC"
    AUDIOBOOK = "AUDIOBOOK"
    MINIMAL = "MINIMAL"


@dataclass
class SubtitleEvent:
    """Individual subtitle event aligned to audio timeline."""

    sequence_index: int
    text: str
    start_time_seconds: float
    end_time_seconds: float
    source_chunk_id: Optional[str] = None
    source_section_id: Optional[str] = None


@dataclass
class SubtitleValidationResult:
    """Validation report for a generated subtitle event sequence."""

    is_valid: bool
    total_events: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
