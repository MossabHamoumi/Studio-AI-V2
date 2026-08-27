"""TTS Domain Models and Value Objects."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TTSProviderType(str, Enum):
    KOKORO = "KOKORO"
    PIPER = "PIPER"
    FAILED = "FAILED"


@dataclass
class TTSVoice:
    """Voice metadata object."""

    provider: TTSProviderType
    voice_id: str
    display_name: str
    language: str = "en-us"
    is_available: bool = True
    sample_rate: int = 24000


@dataclass
class AudioChunk:
    """Individual chunk of synthesized audio."""

    chunk_index: int
    text: str
    word_count: int
    audio_path: str
    duration_seconds: float
    provider_used: TTSProviderType
    voice_id: str
    cache_key: str


@dataclass
class AudioTimelineEntry:
    """Segment entry in full audio narration timeline."""

    sequence_index: int
    text: str
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    audio_file_path: str


@dataclass
class AudioTimeline:
    """Complete assembled audio narration timeline."""

    project_id: str
    chapter_id: str
    total_duration_seconds: float
    assembled_audio_path: str
    entries: List[AudioTimelineEntry] = field(default_factory=list)
