"""Visual Planning and Timeline Specification Service."""

from typing import Dict, List, Optional, Tuple
from src.config.settings import AppSettings
from src.domain.visual_models import (
    MotionEffect,
    OutputProfile,
    ScalingMode,
    TitleCardSpec,
    TransitionEffect,
    VisualMode,
    VisualPlanSpec,
    VisualSegment,
)


class VisualPlanner:
    """Creates visual timeline specifications and editable AI image prompts."""

    PROFILE_DIMENSIONS: Dict[OutputProfile, Tuple[int, int]] = {
        OutputProfile.LANDSCAPE_16_9: (1920, 1080),
        OutputProfile.PORTRAIT_9_16: (1080, 1920),
        OutputProfile.SQUARE_1_1: (1080, 1080),
    }

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def create_visual_plan(
        self,
        project_id: str,
        chapter_id: str,
        mode: VisualMode = VisualMode.STATIC_IMAGE,
        profile: OutputProfile = OutputProfile.LANDSCAPE_16_9,
        scaling: ScalingMode = ScalingMode.COVER,
        motion: MotionEffect = MotionEffect.SLOW_ZOOM,
        background_asset_id: Optional[str] = None,
        gameplay_asset_id: Optional[str] = None,
        title: str = "Story Title",
        subtitle: str = "A Local AI Narration",
        image_prompt: Optional[str] = None,
    ) -> VisualPlanSpec:
        """Construct a complete visual timeline plan specification."""
        width, height = self.PROFILE_DIMENSIONS.get(profile, (1920, 1080))

        if not image_prompt:
            image_prompt = self.generate_editable_image_prompt(
                summary="Dramatic narrative scene",
                characters=["Hero"],
                tone="Dramatic",
                mood="Atmospheric",
                aspect_ratio=profile.value,
            )

        title_card = TitleCardSpec(
            title=title,
            subtitle=subtitle,
            multiline=True,
            safe_bounds=True,
            fade_in_sec=0.5,
            fade_out_sec=0.5,
            hold_sec=3.0,
        )

        return VisualPlanSpec(
            project_id=project_id,
            chapter_id=chapter_id,
            mode=mode,
            profile=profile,
            width=width,
            height=height,
            scaling=scaling,
            motion=motion,
            image_prompt=image_prompt,
            background_asset_id=background_asset_id,
            gameplay_asset_id=gameplay_asset_id,
            gameplay_audio_muted=True,  # Always muted by default
            title_card=title_card,
        )

    def generate_editable_image_prompt(
        self,
        summary: str,
        characters: List[str],
        tone: str,
        mood: str,
        aspect_ratio: str = "16:9",
    ) -> str:
        """Generate AI image prompt string that can be edited by user."""
        char_str = ", ".join(characters) if characters else "a dramatic protagonist"
        return (
            f"High quality cinematic digital art, {tone} tone, {mood} mood. "
            f"Depicting {char_str} in a scene: {summary[:100]}. "
            f"Detailed lighting, 8k resolution, aspect ratio {aspect_ratio} --no text --no watermark"
        )
