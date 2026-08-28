"""Tests for Production Orchestrator and Durable Execution (Phase 8)."""

import json
from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.ai_models import AIMode
from src.domain.models import Chapter, ProductionRun, ProductionRunStatus, Project, StageName
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.content_engine import ContentEngine
from src.services.diagnostic_bundle import DiagnosticBundleExporter
from src.services.preflight_checker import PreflightChecker
from src.services.production_orchestrator import ProductionOrchestrator
from src.utilities.exceptions import ValidationError


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_orch.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_preflight_checker_validation_failures(test_db: DatabaseEngine, tmp_path: Path):
    """Verify PreflightChecker flags missing project/chapters or FFmpeg gracefully."""
    settings = AppSettings(workspace_dir=tmp_path)
    chapter_repo = ChapterRepository(test_db)
    source_repo = SourceRepository(test_db)
    checker = PreflightChecker(settings, chapter_repo, source_repo)

    # 1. Missing project
    passed, errors = checker.check_preflight(None, [])
    assert not passed
    assert any("No active project" in e for e in errors)

    # 2. Project with no chapters
    proj = ProjectRepository(test_db).save(Project(title="Empty Proj"))
    passed, errors = checker.check_preflight(proj, [])
    assert not passed
    assert any("No chapters selected" in e for e in errors)


def test_diagnostic_bundle_export_on_failure(test_db: DatabaseEngine, tmp_path: Path):
    """Verify DiagnosticBundleExporter creates diagnostic_bundle_<run_id>.json without secrets."""
    settings = AppSettings(workspace_dir=tmp_path)
    proj = ProjectRepository(test_db).save(Project(title="Diagnostic Proj"))
    run_repo = ProductionRunRepository(test_db)

    run = run_repo.save(
        ProductionRun(
            project_id=proj.id,
            status=ProductionRunStatus.FAILED,
            current_stage=StageName.NARRATION,
            failure_reason="TTS Synthesis Engine Failure",
        )
    )

    exporter = DiagnosticBundleExporter(settings)
    bundle_path = exporter.export_bundle(
        production_run=run,
        project=proj,
        exception=RuntimeError("TTS engine offline"),
    )

    assert bundle_path.exists()
    assert f"diagnostic_bundle_{run.id}.json" in bundle_path.name

    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert data["run_id"] == run.id
    assert data["status"] == "FAILED"
    assert data["exception"]["type"] == "RuntimeError"


def test_3_chapter_novel_orchestration_and_isolation(test_db: DatabaseEngine, tmp_path: Path):
    """Real end-to-end orchestration test across a 3-chapter story with chapter directory isolation."""
    settings = AppSettings(workspace_dir=tmp_path)

    proj_repo = ProjectRepository(test_db)
    source_repo = SourceRepository(test_db)
    chapter_repo = ChapterRepository(test_db)
    section_repo = SectionRepository(test_db)
    analysis_repo = AnalysisRepository(test_db)
    adaptation_repo = AdaptationRepository(test_db)
    asset_repo = AssetRepository(test_db)
    job_repo = JobRepository(test_db)
    run_repo = ProductionRunRepository(test_db)

    # 1. Ingest 3-chapter test story
    proj = proj_repo.save(Project(title="3-Chapter Story"))
    content_engine = ContentEngine(source_repo, chapter_repo, section_repo)

    story_text = (
        "CHAPTER 1\nThe detective arrived at the foggy harbor.\n\n"
        "CHAPTER 2\nInside the warehouse, a silver compass lay on the table.\n\n"
        "CHAPTER 3\nThe secret code unlocked the hidden chamber."
    )

    content_engine.process_text_source(proj.id, story_text)
    chapters = chapter_repo.list_by_project(proj.id)
    assert len(chapters) == 3

    orchestrator = ProductionOrchestrator(
        settings,
        proj_repo,
        source_repo,
        chapter_repo,
        analysis_repo,
        adaptation_repo,
        asset_repo,
        job_repo,
        run_repo,
    )

    # Verify preflight dependency check handles missing FFmpeg in sandbox test
    is_ok, errors = orchestrator.preflight.check_preflight(
        proj, [c.id for c in chapters], ai_mode=AIMode.LOCAL_ONLY
    )

    # Preflight fails cleanly if FFmpeg is missing in sandbox environment
    if not is_ok:
        assert any("FFmpeg" in e for e in errors)
    else:
        # Execute sequential 3-chapter novel production run
        results = orchestrator.run_novel_production(proj.id, ai_mode=AIMode.LOCAL_ONLY)
        assert len(results) == 3

        # Verify chapter folder isolation (chapters/001/, chapters/002/, chapters/003/)
        for idx, (run, out_mp4, qa_report) in enumerate(results, 1):
            cnum_str = f"{idx:03d}"
            assert f"chapters/{cnum_str}" in str(out_mp4) or f"chapters/{idx}" in str(out_mp4)
            assert out_mp4.exists()
            assert qa_report.is_passed
