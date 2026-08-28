"""Tests for Audio-Driven Subtitle Engine (Phase 5)."""

from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.domain.subtitle_models import (
    SubtitleEvent,
    SubtitleStyleProfile,
)
from src.domain.tts_models import AudioTimeline, AudioTimelineEntry
from src.services.ass_generator import ASSGenerator
from src.services.srt_generator import SRTGenerator
from src.services.subtitle_engine import SubtitleEngine
from src.services.subtitle_formatter import SubtitleFormatter
from src.services.subtitle_validator import SubtitleValidator
from src.utilities.exceptions import ValidationError


def test_subtitle_validator_bounds_and_overlap():
    validator = SubtitleValidator()

    # Valid non-overlapping events
    events = [
        SubtitleEvent(sequence_index=0, text="First event", start_time_seconds=0.0, end_time_seconds=2.5),
        SubtitleEvent(sequence_index=1, text="Second event", start_time_seconds=2.5, end_time_seconds=5.0),
    ]
    res = validator.validate_subtitle_events(events, max_audio_duration=5.0)
    assert res.is_valid
    assert len(res.errors) == 0

    # Invalid: Overlapping events
    overlapping_events = [
        SubtitleEvent(sequence_index=0, text="First event", start_time_seconds=0.0, end_time_seconds=3.0),
        SubtitleEvent(sequence_index=1, text="Second event", start_time_seconds=2.0, end_time_seconds=5.0),
    ]
    res_overlap = validator.validate_subtitle_events(overlapping_events, max_audio_duration=5.0)
    assert not res_overlap.is_valid
    assert any("Overlaps" in err for err in res_overlap.errors)

    # Invalid: Negative start time
    negative_events = [
        SubtitleEvent(sequence_index=0, text="Negative start", start_time_seconds=-1.0, end_time_seconds=2.0),
    ]
    res_neg = validator.validate_subtitle_events(negative_events, max_audio_duration=5.0)
    assert not res_neg.is_valid


def test_subtitle_formatter_line_wrapping_and_roman_numerals():
    formatter = SubtitleFormatter()

    # Word boundary wrapping
    long_text = "The quick brown fox jumps over the lazy sleeping dog near the riverbank."
    wrapped = formatter.wrap_text(long_text, max_line_len=30, max_lines=2)
    lines = wrapped.split("\n")
    assert len(lines) <= 2
    for line in lines:
        assert len(line) <= 45  # Word boundaries preserved without word truncation

    # Roman Numeral Normalization for narration subtitles
    raw_heading = "In Chapter III, the hero encountered Part II of the puzzle."
    normalized = formatter.normalize_roman_numerals(raw_heading)
    assert "Chapter 3" in normalized
    assert "Part 2" in normalized

    # Gutenberg metadata filtering
    gutenberg_text = (
        "*** START OF THIS PROJECT GUTENBERG EBOOK THE ODYSSEY ***\n"
        "Tell me, O Muse, of that ingenious hero who traveled far and wide."
    )
    filtered = formatter.filter_gutenberg_metadata(gutenberg_text)
    assert "PROJECT GUTENBERG" not in filtered
    assert "Tell me, O Muse" in filtered


def test_ass_generator_an5_center_alignment(tmp_path: Path):
    ass_gen = ASSGenerator()
    events = [
        SubtitleEvent(sequence_index=0, text=r"Center \N Subtitle", start_time_seconds=1.0, end_time_seconds=3.5)
    ]
    out_path = tmp_path / "test_an5.ass"
    ass_gen.generate_ass(events, out_path, style_profile=SubtitleStyleProfile.SHORT_FORM)

    content = out_path.read_text(encoding="utf-8")
    assert r"\an5" in content or "Alignment,10,10,10,1" in content or "Style: Default" in content
    assert "Dialogue: 0,0:00:01.00,0:00:03.50" in content
    assert r"Center \N Subtitle" in content


def test_srt_generator_standard_format(tmp_path: Path):
    srt_gen = SRTGenerator()
    events = [
        SubtitleEvent(sequence_index=0, text="Hello world", start_time_seconds=0.0, end_time_seconds=2.345)
    ]
    out_path = tmp_path / "test.srt"
    srt_gen.generate_srt(events, out_path)

    content = out_path.read_text(encoding="utf-8")
    assert "1\n00:00:00,000 --> 00:00:02,345\nHello world" in content


def test_audio_driven_subtitle_engine_pipeline(tmp_path: Path):
    settings = AppSettings(workspace_dir=tmp_path)
    engine = SubtitleEngine(settings)

    # Real Audio Timeline
    timeline = AudioTimeline(
        project_id="proj-sub-1",
        chapter_id="chap-sub-1",
        total_duration_seconds=10.0,
        assembled_audio_path=str(tmp_path / "assembled.wav"),
        entries=[
            AudioTimelineEntry(
                sequence_index=0,
                text="In Chapter I, the adventure began in the quiet valley.",
                start_time_seconds=0.0,
                end_time_seconds=4.5,
                duration_seconds=4.5,
                audio_file_path=str(tmp_path / "chunk1.wav"),
            ),
            AudioTimelineEntry(
                sequence_index=1,
                text="The hero found the ancient map hidden inside the library.",
                start_time_seconds=4.5,
                end_time_seconds=10.0,
                duration_seconds=5.5,
                audio_file_path=str(tmp_path / "chunk2.wav"),
            ),
        ],
    )

    ass_file, srt_file, val_res = engine.generate_subtitles_from_audio_timeline(timeline)

    assert val_res.is_valid
    assert ass_file.exists()
    assert srt_file.exists()

    ass_text = ass_file.read_text(encoding="utf-8")
    # Verify Roman numeral normalization in generated ASS subtitle
    assert "Chapter 1" in ass_text
    assert "Dialogue: 0,0:00:00.00,0:00:04.50" in ass_text
