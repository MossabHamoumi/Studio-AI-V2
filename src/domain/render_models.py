"""Render Domain Models and QA Specifications."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.domain.models import current_utc_timestamp, generate_uuid
from src.domain.visual_models import OutputProfile, ScalingMode, TitleCardSpec, VisualMode


@dataclass
class RenderSpec:
    """Render Specification container for FFmpeg pipeline."""

    project_id: str
    chapter_id: str
    output_path: str
    narration_audio_path: str
    target_duration_seconds: float
    width: int = 1920
    height: int = 1080
    fps: int = 30
    visual_mode: VisualMode = VisualMode.STATIC_IMAGE
    scaling_mode: ScalingMode = ScalingMode.COVER
    background_image_path: Optional[str] = None
    gameplay_video_path: Optional[str] = None
    gameplay_audio_muted: bool = True
    subtitle_ass_path: Optional[str] = None
    title_card: Optional[TitleCardSpec] = None
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class QAReport:
    """Media QA Report for rendered MP4 video output."""

    render_spec_id: str
    output_path: str
    is_passed: bool
    video_stream_ok: bool
    audio_stream_ok: bool
    resolution_ok: bool
    fps_ok: bool
    duration_sync_ok: bool
    subtitle_present: bool
    measured_duration_sec: float
    measured_width: int
    measured_height: int
    measured_fps: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=current_utc_timestamp)
