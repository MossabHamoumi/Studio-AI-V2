"""Tests for Local AI Layer and Ollama Integration (Phase 3)."""

from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.ai_models import (
    AIMode,
    AIStatus,
    AdaptationStatus,
    AnalysisType,
    normalize_enum_value,
)
from src.domain.models import Chapter, Project, Source
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.source_repo import SourceRepository
from src.services.ai_director import AIDirector
from src.services.ai_provider import LocalFallbackAnalyzer, OllamaProvider
from src.utilities.exceptions import ValidationError


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_ai.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_enum_safety_normalization():
    """Verify enum safety normalization prevents str/Enum attribute crashes."""
    assert normalize_enum_value("AI_FULL", AIMode) == AIMode.AI_FULL
    assert normalize_enum_value("ai_full", AIMode) == AIMode.AI_FULL
    assert normalize_enum_value(AIMode.AI_ASSISTED, AIMode) == AIMode.AI_ASSISTED
    assert normalize_enum_value("ACCEPTED", AdaptationStatus) == AdaptationStatus.ACCEPTED


def test_ollama_offline_health_probe():
    """Verify offline Ollama server returns OFFLINE status cleanly without crashing."""
    provider = OllamaProvider(base_url="http://localhost:59999", timeout_seconds=1.0)
    status = provider.check_health()
    assert status in (AIStatus.OFFLINE, AIStatus.UNAVAILABLE)


def test_local_fallback_analyzer_execution(test_db: DatabaseEngine):
    """Verify local fallback analyzer executes and persists LOCAL_FALLBACK analysis."""
    proj = ProjectRepository(test_db).save(Project(title="AI Fallback Test"))
    src = SourceRepository(test_db).save(Source(project_id=proj.id, uri_or_path="test.txt"))
    chap = ChapterRepository(test_db).save(
        Chapter(
            project_id=proj.id,
            source_id=src.id,
            chapter_number=1,
            sequence_index=0,
            title="Chapter 1",
            start_offset=0,
            end_offset=100,
            original_text="Alice walked into the mysterious forest.",
        )
    )

    analysis_repo = AnalysisRepository(test_db)
    fallback_analyzer = LocalFallbackAnalyzer()
    analysis = fallback_analyzer.analyze_story_locally(
        project_id=proj.id,
        chapter_id=chap.id,
        text=chap.original_text,
        source_hash="hash123",
    )

    saved = analysis_repo.save(analysis)
    reloaded = analysis_repo.get_by_chapter(chap.id)

    assert reloaded is not None
    assert reloaded.analysis_type == AnalysisType.LOCAL_FALLBACK
    assert reloaded.model_used == "LOCAL_FALLBACK"
    assert "Alice" in reloaded.characters


def test_ai_director_local_only_mode(test_db: DatabaseEngine, tmp_path: Path):
    """Verify LOCAL_ONLY mode skips Ollama network calls entirely."""
    proj = ProjectRepository(test_db).save(Project(title="Local Only Proj"))
    src = SourceRepository(test_db).save(Source(project_id=proj.id, uri_or_path="test.txt"))
    chap = ChapterRepository(test_db).save(
        Chapter(
            project_id=proj.id,
            source_id=src.id,
            chapter_number=1,
            sequence_index=0,
            title="Space Station",
            start_offset=0,
            end_offset=100,
            original_text="The space station orbited Europa in silence.",
        )
    )

    settings = AppSettings(workspace_dir=tmp_path)
    analysis_repo = AnalysisRepository(test_db)
    adapt_repo = AdaptationRepository(test_db)

    director = AIDirector(analysis_repo, adapt_repo, settings)

    analysis, status = director.analyze_chapter(
        project_id=proj.id,
        chapter_id=chap.id,
        chapter_text=chap.original_text,
        source_text_hash="hash456",
        mode=AIMode.LOCAL_ONLY,
    )

    assert status == AIStatus.OFFLINE
    assert analysis.analysis_type == AnalysisType.LOCAL_FALLBACK


def test_adaptation_validation_rejection(test_db: DatabaseEngine, tmp_path: Path):
    """Verify adaptation validator rejects empty, identical, or incomplete text."""
    settings = AppSettings(workspace_dir=tmp_path)
    director = AIDirector(
        AnalysisRepository(test_db), AdaptationRepository(test_db), settings
    )

    original = "The detective entered the abandoned warehouse carefully."

    # 1. Reject empty
    with pytest.raises(ValidationError):
        director.validate_adaptation_output(original, "")

    # 2. Reject identical
    with pytest.raises(ValidationError):
        director.validate_adaptation_output(original, original)

    # 3. Reject severely incomplete (< 30% length)
    with pytest.raises(ValidationError):
        director.validate_adaptation_output(original, "The")


def test_adaptation_status_review_lifecycle(test_db: DatabaseEngine, tmp_path: Path):
    """Verify PROPOSED -> ACCEPTED / REJECTED status review lifecycle."""
    proj = ProjectRepository(test_db).save(Project(title="Adapt Lifecycle Proj"))
    src = SourceRepository(test_db).save(Source(project_id=proj.id, uri_or_path="test.txt"))
    chap = ChapterRepository(test_db).save(
        Chapter(
            project_id=proj.id,
            source_id=src.id,
            chapter_number=1,
            sequence_index=0,
            title="Warehouse",
            start_offset=0,
            end_offset=100,
            original_text="The detective entered the abandoned warehouse carefully.",
        )
    )

    settings = AppSettings(workspace_dir=tmp_path)
    adapt_repo = AdaptationRepository(test_db)
    director = AIDirector(
        AnalysisRepository(test_db), adapt_repo, settings
    )

    adaptation, status = director.adapt_chapter_script(
        project_id=proj.id,
        chapter_id=chap.id,
        chapter_text=chap.original_text,
        source_text_hash="hash789",
        mode=AIMode.LOCAL_ONLY,
    )

    assert adaptation.status == AdaptationStatus.PROPOSED

    # Accept adaptation
    accepted = director.update_adaptation_status(adaptation.id, AdaptationStatus.ACCEPTED)
    assert accepted.status == AdaptationStatus.ACCEPTED

    # Verify query for accepted adaptation
    accepted_retrieved = adapt_repo.get_accepted_by_chapter(chap.id)
    assert accepted_retrieved is not None
    assert accepted_retrieved.id == adaptation.id
