"""AI Domain Models and Enum Normalization Utilities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar
from src.domain.models import current_utc_timestamp, generate_uuid

T = TypeVar("T", bound=Enum)


def normalize_enum_value(val: Any, enum_class: Type[T], default: Optional[T] = None) -> T:
    """Safely normalize strings, Enum instances, or display labels into an Enum member.

    Prevents crashes like: "'str' object has no attribute 'value'".
    """
    if isinstance(val, enum_class):
        return val

    if isinstance(val, Enum):
        # Different enum or raw value
        val_str = str(val.value)
    else:
        val_str = str(val).strip()

    # Try matching value or name
    for member in enum_class:
        if member.value.upper() == val_str.upper() or member.name.upper() == val_str.upper():
            return member

    if default is not None:
        return default

    raise ValueError(f"Cannot normalize '{val}' to enum {enum_class.__name__}")


class AIMode(str, Enum):
    AI_FULL = "AI_FULL"
    AI_ASSISTED = "AI_ASSISTED"
    LOCAL_ONLY = "LOCAL_ONLY"


class AIStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    OFFLINE = "OFFLINE"


class AnalysisType(str, Enum):
    AI_RESULT = "AI_RESULT"
    LOCAL_FALLBACK = "LOCAL_FALLBACK"


class AdaptationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass
class Analysis:
    """Structured Analysis entity."""

    project_id: str
    chapter_id: str
    summary: str
    characters: List[str] = field(default_factory=list)
    character_details: Dict[str, Any] = field(default_factory=dict)
    locations: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    tone: str = "Neutral"
    mood: str = "Dramatic"
    themes: List[str] = field(default_factory=list)
    dialogue: List[Dict[str, Any]] = field(default_factory=list)
    narration: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    visual_opportunities: List[str] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    analysis_type: AnalysisType = AnalysisType.AI_RESULT
    model_used: str = "qwen3:8b"
    source_text_hash: str = ""
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class Adaptation:
    """Listener/Story Adaptation entity."""

    project_id: str
    chapter_id: str
    adapted_text: str
    source_text_hash: str
    model_used: str = "qwen3:8b"
    status: AdaptationStatus = AdaptationStatus.PROPOSED
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    updated_at: str = field(default_factory=current_utc_timestamp)
