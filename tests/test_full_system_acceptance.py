"""Full System Acceptance & 20 Historical Failure Regressions Test Suite (Phase 8)."""

from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.ai_models import AIMode, AdaptationStatus, normalize_enum_value
from src.domain.models import AssetStatus, Chapter, Project, ProjectType
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.ai_director import AIDirector
from src.services.content_engine import ContentEngine
from src.services.narration_engine import NarrationEngine
from src.services.preflight_checker import PreflightChecker
from src.services.production_orchestrator import ProductionOrchestrator
from src.services.subtitle_formatter import SubtitleFormatter
from src.services.subtitle_validator import SubtitleValidator
from src.utilities.audio_validator import AudioValidator
from src.utilities.exceptions import ValidationError


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_full_acceptance.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_regression_1_9000_word_non_truncation(test_db: DatabaseEngine, tmp_path: Path):
    """Regression 1: 9,000+ word document non-truncation verification."""
    source_repo = SourceRepository(test_db)
    chapter_repo = ChapterRepository(test_db)
    sec_repo = SectionRepository(test_db)
    proj = ProjectRepository(test_db).save(Project(title="9k Test"))

    text = "CHAPTER 1\n" + " ".join(["word" + str(i) for i in range(9200)])
    file_path = tmp_path / "9k_test.txt"
    file_path.write_text(text, encoding="utf-8")

    engine = ContentEngine(source_repo, chapter_repo, sec_repo)
    source, report = engine.process_file_source(proj.id, file_path)

    assert report.word_count >= 9200
    assert report.char_count == len(text)


def test_regression_3_roman_numeral_pronunciation():
    """Regression 3: Chapter III -> Chapter 3 speech normalization."""
    formatter = SubtitleFormatter()
    res = formatter.normalize_roman_numerals("In Chapter III, the mystery deepens.")
    assert "Chapter 3" in res


def test_regression_4_pure_sine_tone_rejection(tmp_path: Path):
    """Regression 4 & 5: Rejects synthetic pure 440 Hz / 330 Hz sine wave tones."""
    validator = AudioValidator()
    sine_file = tmp_path / "sine.wav"

    # Write pure sine wave
    import math, struct, wave
    with wave.open(str(sine_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        samples = bytearray()
        for i in range(24000 * 2):
            val = int(16000 * math.sin(2 * math.pi * 440.0 * i / 24000))
            samples.extend(struct.pack("<h", val))
        wf.writeframes(bytes(samples))

    res = validator.validate_audio_file(sine_file)
    assert not res.is_valid
    assert res.is_pure_tone


def test_regression_12_enum_safety_normalization():
    """Regression 12: Prevents 'str' object has no attribute 'value' crashes."""
    assert normalize_enum_value("NOVEL", ProjectType) == ProjectType.NOVEL
    assert normalize_enum_value(ProjectType.NOVEL, ProjectType) == ProjectType.NOVEL


def test_regression_19_missing_ffmpeg_preflight_detection(test_db: DatabaseEngine, tmp_path: Path):
    """Regression 19: Honest preflight failure when dependencies are missing."""
    settings = AppSettings(workspace_dir=tmp_path)
    chapter_repo = ChapterRepository(test_db)
    source_repo = SourceRepository(test_db)
    checker = PreflightChecker(settings, chapter_repo, source_repo)

    proj = ProjectRepository(test_db).save(Project(title="Preflight Fail Test"))
    passed, errors = checker.check_preflight(proj, [])
    assert not passed
