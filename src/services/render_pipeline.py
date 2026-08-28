"""Render Pipeline Orchestrator.

Orchestrates RenderSpec validation, FFmpeg rendering, Media QA validation,
and asset registration upon QA PASS.
"""

from pathlib import Path
from typing import Callable, Optional, Tuple
from src.config.settings import AppSettings
from src.domain.models import Asset, AssetType
from src.domain.render_models import QAReport, RenderSpec
from src.repositories.asset_repo import AssetRepository
from src.services.ffmpeg_renderer import FFmpegRenderer
from src.services.media_qa import MediaQAValidator
from src.utilities.exceptions import StudioAIError, ValidationError


class RenderPipeline:
    """Hardened Render Pipeline coordinating rendering and QA validation."""

    def __init__(self, settings: AppSettings, asset_repo: AssetRepository):
        self.settings = settings
        self.asset_repo = asset_repo
        self.renderer = FFmpegRenderer()
        self.qa_validator = MediaQAValidator()

    def execute_render_pipeline(
        self,
        spec: RenderSpec,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Tuple[Path, QAReport]:
        """Execute full render pipeline with QA validation."""
        # 1. Preflight Validation
        narration_path = Path(spec.narration_audio_path)
        if not narration_path.exists():
            raise ValidationError(f"Render failed: narration audio path '{spec.narration_audio_path}' does not exist.")

        if spec.subtitle_ass_path and not Path(spec.subtitle_ass_path).exists():
            raise ValidationError(f"Render failed: subtitle ASS file '{spec.subtitle_ass_path}' does not exist.")

        # 2. Render MP4 via FFmpeg
        output_file = self.renderer.render(spec, progress_callback=progress_callback)

        # 3. Media QA Validation
        qa_report = self.qa_validator.validate_render_output(spec, output_file)

        if not qa_report.is_passed:
            err_msg = "; ".join(qa_report.errors)
            raise StudioAIError(f"Render QA Failed: {err_msg}")

        # 4. Register Video Asset in SQLite upon QA PASS
        video_asset = Asset(
            project_id=spec.project_id,
            asset_type=AssetType.VIDEO,
            path=str(output_file),
            size_bytes=output_file.stat().st_size,
            metadata={
                "duration_seconds": qa_report.measured_duration_sec,
                "resolution": f"{qa_report.measured_width}x{qa_report.measured_height}",
                "width": qa_report.measured_width,
                "height": qa_report.measured_height,
                "fps": qa_report.measured_fps,
                "qa_passed": True,
            },
        )
        self.asset_repo.register_asset(video_asset)

        return output_file, qa_report

    def cancel_render(self) -> None:
        """Cancel active rendering process."""
        self.renderer.cancel_render()
