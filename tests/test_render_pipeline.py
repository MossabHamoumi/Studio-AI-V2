"""Tests for Hardened FFmpeg Render Pipeline and Media QA (Phase 7)."""

import json
import shutil
import subprocess
from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.render_models import RenderSpec
from src.domain.visual_models import TitleCardSpec, VisualMode
from src.repositories.asset_repo import AssetRepository
from src.services.command_builder import FFmpegCommandBuilder
from src.services.filter_graph import FilterGraphBuilder
from src.services.media_qa import MediaQAValidator
from src.services.render_pipeline import RenderPipeline
from src.utilities.exceptions import ValidationError


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_render.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_filter_graph_builder_ass_escaping_and_title_card():
    """Verify FilterGraphBuilder generates valid filter complex with escaped ASS paths and title cards."""
    builder = FilterGraphBuilder()

    spec = RenderSpec(
        project_id="proj-r1",
        chapter_id="chap-r1",
        output_path="/tmp/output.mp4",
        narration_audio_path="/tmp/narration.wav",
        target_duration_seconds=10.0,
        subtitle_ass_path="C:/StudioAI/chapters/chap-1/subtitles/narration.ass",
        title_card=TitleCardSpec(title="Test Title"),
    )

    filter_str, v_map, a_map = builder.build_filter_graph(spec)

    assert v_map == "[v]"
    assert a_map == "1:a"
    assert "scale=1920:1080" in filter_str
    assert "ass=" in filter_str
    assert "drawtext=" in filter_str


def test_command_builder_explicit_mapping_and_nostdin():
    """Verify FFmpegCommandBuilder includes explicit stream maps and -nostdin flags."""
    builder = FFmpegCommandBuilder()

    spec = RenderSpec(
        project_id="proj-r2",
        chapter_id="chap-r2",
        output_path="/tmp/out.mp4",
        narration_audio_path="/tmp/audio.wav",
        target_duration_seconds=15.0,
        background_image_path="/tmp/bg.png",
    )

    cmd = builder.build_command(spec)

    assert "-nostdin" in cmd
    assert "-progress" in cmd
    assert "-map" in cmd
    assert "[v]" in cmd
    assert "1:a" in cmd
    assert "-c:v" in cmd
    assert "libx264" in cmd
    assert "-c:a" in cmd
    assert "aac" in cmd


def test_render_pipeline_preflight_missing_narration_validation(test_db: DatabaseEngine, tmp_path: Path):
    """Verify RenderPipeline preflight validation rejects missing narration audio."""
    settings = AppSettings(workspace_dir=tmp_path)
    asset_repo = AssetRepository(test_db)
    pipeline = RenderPipeline(settings, asset_repo)

    missing_audio_spec = RenderSpec(
        project_id="proj-r3",
        chapter_id="chap-r3",
        output_path=str(tmp_path / "out.mp4"),
        narration_audio_path=str(tmp_path / "missing_audio.wav"),
        target_duration_seconds=10.0,
    )

    with pytest.raises(ValidationError) as exc_info:
        pipeline.execute_render_pipeline(missing_audio_spec)

    assert "narration audio path" in str(exc_info.value).lower()


def test_media_qa_validator_missing_file_report(tmp_path: Path):
    """Verify MediaQAValidator writes failed qa_report.json for missing output files."""
    qa_val = MediaQAValidator()

    spec = RenderSpec(
        project_id="proj-r4",
        chapter_id="chap-r4",
        output_path=str(tmp_path / "missing_render.mp4"),
        narration_audio_path="/tmp/audio.wav",
        target_duration_seconds=5.0,
    )

    report = qa_val.validate_render_output(spec, tmp_path / "missing_render.mp4")

    assert not report.is_passed
    assert not report.video_stream_ok
    assert len(report.errors) >= 1

    report_file = tmp_path / "qa_report.json"
    assert report_file.exists()

    report_json = json.loads(report_file.read_text(encoding="utf-8"))
    assert report_json["is_passed"] is False


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg CLI binary not installed on system")
def test_real_ffmpeg_end_to_end_rendering(test_db: DatabaseEngine, tmp_path: Path):
    """Real end-to-end FFmpeg rendering test if FFmpeg is installed on system."""
    settings = AppSettings(workspace_dir=tmp_path)
    asset_repo = AssetRepository(test_db)
    pipeline = RenderPipeline(settings, asset_repo)

    # Generate dummy WAV audio file
    audio_path = tmp_path / "test_audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(audio_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Generate dummy BG image file
    image_path = tmp_path / "test_bg.png"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=1920x1080", "-vframes", "1", str(image_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    output_path = tmp_path / "rendered_output.mp4"

    spec = RenderSpec(
        project_id="proj-real",
        chapter_id="chap-real",
        output_path=str(output_path),
        narration_audio_path=str(audio_path),
        background_image_path=str(image_path),
        target_duration_seconds=2.0,
        width=1920,
        height=1080,
        fps=30,
        visual_mode=VisualMode.STATIC_IMAGE,
    )

    out_file, qa_report = pipeline.execute_render_pipeline(spec)

    assert out_file.exists()
    assert qa_report.is_passed
    assert qa_report.video_stream_ok
    assert qa_report.audio_stream_ok
