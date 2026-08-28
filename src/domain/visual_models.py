"""Visual Domain Models and Specifications."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from src.domain.models import current_utc_timestamp, generate_uuid


class VisualMode(str, Enum):
    STATIC_IMAGE = "STATIC_IMAGE"
    MULTI_IMAGE = "MULTI_IMAGE"
    GAMEPLAY = "GAMEPLAY"
    MIXED = "MIXED"
    NONE = "NONE"


class OutputProfile(str, Enum):
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"
    SQUARE_1_1 = "1:1"


class ScalingMode(str, Enum):
    COVER = "COVER"
    CONTAIN = "CONTAIN"
    STRETCH = "STRETCH"


class MotionEffect(str, Enum):
    NONE = "NONE"
    SLOW_ZOOM = "SLOW_ZOOM"
    PAN = "PAN"
    KEN_BURNS = "KEN_BURNS"


class TransitionEffect(str, Enum):
    FADE = "FADE"
    CROSSFADE = "CROSSFADE"
    FADE_TO_BLACK = "FADE_TO_BLACK"


@dataclass
class VisualSegment:
    """Timeline visual segment spec."""

    sequence_index: int
    asset_id: str
    start_time_seconds: float
    end_time_seconds: float
    transition: TransitionEffect = TransitionEffect.CROSSFADE


@dataclass
class TitleCardSpec:
    """Title card overlay spec."""

    title: str
    subtitle: str = ""
    multiline: bool = True
    safe_bounds: bool = True
    fade_in_sec: float = 0.5
    fade_out_sec: float = 0.5
    hold_sec: float = 3.0


@dataclass
class VisualPlanSpec:
    """Complete Visual Timeline Specification."""

    project_id: str
    chapter_id: str
    mode: VisualMode = VisualMode.STATIC_IMAGE
    profile: OutputProfile = OutputProfile.LANDSCAPE_16_9
    width: int = 1920
    height: int = 1080
    scaling: ScalingMode = ScalingMode.COVER
    motion: MotionEffect = MotionEffect.SLOW_ZOOM
    image_prompt: str = ""
    background_asset_id: Optional[str] = None
    gameplay_asset_id: Optional[str] = None
    gameplay_audio_muted: bool = True
    title_card: Optional[TitleCardSpec] = None
    segments: List[VisualSegment] = field(default_factory=list)
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
