"""Audio-Driven Subtitle Engine.

Transforms real AudioTimeline segments into validated ASS and SRT subtitle files.
"""

from pathlib import Path
from typing import List, Tuple
from src.config.settings import AppSettings
from src.domain.subtitle_models import (
    SubtitleEvent,
    SubtitleFormat,
    SubtitleStyleProfile,
    SubtitleValidationResult,
)
from src.domain.tts_models import AudioTimeline
from src.services.ass_generator import ASSGenerator
from src.services.srt_generator import SRTGenerator
from src.services.subtitle_formatter import SubtitleFormatter
from src.services.subtitle_validator import SubtitleValidator
from src.utilities.exceptions import ValidationError


class SubtitleEngine:
    """Audio-driven subtitle generation and validation engine."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.formatter = SubtitleFormatter()
        self.validator = SubtitleValidator()
        self.ass_gen = ASSGenerator()
        self.srt_gen = SRTGenerator()

    def generate_subtitles_from_audio_timeline(
        self,
        timeline: AudioTimeline,
        style_profile: SubtitleStyleProfile = SubtitleStyleProfile.DEFAULT,
        max_line_len: int = 36,
        max_lines: int = 2,
    ) -> Tuple[Path, Path, SubtitleValidationResult]:
        """Generate ASS and SRT subtitle files from real audio timeline."""
        events: List[SubtitleEvent] = []

        for entry in timeline.entries:
            # 1. Filter Gutenberg boilerplate metadata
            clean_text = self.formatter.filter_gutenberg_metadata(entry.text)
            if not clean_text.strip():
                continue

            # 2. Apply narration-only Roman numeral normalization
            normalized_text = self.formatter.normalize_roman_numerals(clean_text)

            # 3. Apply word-boundary line wrapping
            wrapped_text = self.formatter.wrap_text(normalized_text, max_line_len=max_line_len, max_lines=max_lines)

            # 4. Construct SubtitleEvent bound directly to real audio timeline timing
            event = SubtitleEvent(
                sequence_index=entry.sequence_index,
                text=wrapped_text,
                start_time_seconds=entry.start_time_seconds,
                end_time_seconds=entry.end_time_seconds,
                source_chunk_id=entry.audio_file_path,
            )
            events.append(event)

        # 5. Dedicated Subtitle Validation
        val_res = self.validator.validate_subtitle_events(events, max_audio_duration=timeline.total_duration_seconds)
        if not val_res.is_valid:
            err_msg = "; ".join(val_res.errors)
            raise ValidationError(f"Subtitle validation failed: {err_msg}")

        # 6. Generate ASS and SRT subtitle files on disk
        project_dir = self.settings.get_project_dir(timeline.project_id)
        sub_dir = project_dir / "chapters" / timeline.chapter_id / "subtitles"
        sub_dir.mkdir(parents=True, exist_ok=True)

        ass_path = sub_dir / "narration.ass"
        srt_path = sub_dir / "narration.srt"

        self.ass_gen.generate_ass(events, ass_path, style_profile=style_profile)
        self.srt_gen.generate_srt(events, srt_path)

        return ass_path, srt_path, val_res
