"""Tests for Visual Engine and Local Asset Library (Phase 6)."""

from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.models import AssetStatus, AssetType, Project
from src.domain.visual_models import (
    MotionEffect,
    OutputProfile,
    ScalingMode,
    VisualMode,
)
from src.repositories.asset_repo import AssetRepository
from src.repositories.project_repo import ProjectRepository
from src.services.asset_library import AssetLibraryService
from src.services.ffprobe_inspector import FFprobeInspector
from src.services.visual_planner import VisualPlanner


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_visual.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_ffprobe_inspector_missing_file_handling(tmp_path: Path):
    """Verify FFprobeInspector gracefully flags missing files as exists=False without crashing."""
    inspector = FFprobeInspector()
    missing_file = tmp_path / "non_existent_video.mp4"

    res = inspector.probe_media_file(missing_file)
    assert not res.exists
    assert res.duration_seconds == 0.0
    assert "does not exist" in res.error_message


def test_asset_library_registration_and_missing_recovery(test_db: DatabaseEngine, tmp_path: Path):
    """Verify AssetLibraryService registers assets and flags missing files."""
    asset_repo = AssetRepository(test_db)
    proj_repo = ProjectRepository(test_db)
    proj = proj_repo.save(Project(title="Visual Asset Test"))

    service = AssetLibraryService(asset_repo)

    # 1. Valid image file
    image_file = tmp_path / "bg_image.png"
    image_file.write_bytes(b"dummy_image_data_bytes")

    registered = service.register_media_asset(
        project_id=proj.id,
        file_path=image_file,
        asset_type=AssetType.IMAGE,
        category="backgrounds",
    )

    assert registered.status == AssetStatus.VALIDATED
    assert registered.metadata["category"] == "backgrounds"

    # 2. Simulate missing asset file
    image_file.unlink()
    rechecked = service.verify_asset_status(registered.id)
    assert rechecked.status == AssetStatus.FAILED
    assert rechecked.metadata.get("missing") is True


def test_gameplay_looping_calculation():
    """Verify gameplay looping calculation for matching narration duration."""
    service = AssetLibraryService(None)
    # 30 second gameplay video for a 75 second narration
    loops, duration = service.calculate_gameplay_looping(gameplay_duration=30.0, target_narration_duration=75.0)

    assert loops == 3
    assert duration == 75.0


def test_visual_planner_dimensions_and_prompt_generation(tmp_path: Path):
    """Verify VisualPlanner produces correct output dimensions and editable AI prompts."""
    settings = AppSettings(workspace_dir=tmp_path)
    planner = VisualPlanner(settings)

    # 1. Portrait 9:16 Short Reel Profile
    plan_reel = planner.create_visual_plan(
        project_id="proj-v1",
        chapter_id="chap-v1",
        mode=VisualMode.GAMEPLAY,
        profile=OutputProfile.PORTRAIT_9_16,
        title="Reel Title",
    )

    assert plan_reel.width == 1080
    assert plan_reel.height == 1920
    assert plan_reel.gameplay_audio_muted is True
    assert plan_reel.title_card.title == "Reel Title"

    # 2. Editable AI Image Prompt
    prompt = planner.generate_editable_image_prompt(
        summary="Detective solving a case in the rain",
        characters=["Detective Smith"],
        tone="Dark",
        mood="Suspenseful",
        aspect_ratio="16:9",
    )

    assert "Detective Smith" in prompt
    assert "Dark" in prompt
    assert "aspect ratio 16:9" in prompt
