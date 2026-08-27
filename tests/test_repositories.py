"""Integration tests for repositories, persistence, isolation, and crash recovery."""

from pathlib import Path
import pytest
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.models import (
    Asset,
    AssetStatus,
    AssetType,
    Chapter,
    ChapterStatus,
    Job,
    JobStatus,
    JobType,
    ProductionRun,
    ProductionRunStatus,
    Project,
    ProjectType,
    Section,
    SectionType,
    Source,
    SourceType,
)
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_repo.db"
    engine = DatabaseEngine(db_file)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()
    yield engine
    engine.close()


def test_project_save_close_reopen_reload(tmp_path: Path):
    db_file = tmp_path / "test_reload.db"

    # Step 1: Create project and save
    engine1 = DatabaseEngine(db_file)
    MigrationRunner(engine1).apply_migrations()
    repo1 = ProjectRepository(engine1)

    project = Project(title="Persistent Story", project_type=ProjectType.SHORT_STORY)
    repo1.save(project)
    project_id = project.id
    engine1.close()

    # Step 2: Reopen DB with fresh connection and reload
    engine2 = DatabaseEngine(db_file)
    repo2 = ProjectRepository(engine2)
    reloaded = repo2.get_by_id(project_id)

    assert reloaded.id == project_id
    assert reloaded.title == "Persistent Story"
    assert reloaded.project_type == ProjectType.SHORT_STORY
    engine2.close()


def test_project_data_isolation(test_db: DatabaseEngine):
    proj_repo = ProjectRepository(test_db)
    source_repo = SourceRepository(test_db)
    chapter_repo = ChapterRepository(test_db)

    # Create Project A
    proj_a = proj_repo.save(Project(title="Project A"))
    src_a = source_repo.save(Source(project_id=proj_a.id, uri_or_path="/path/a.txt"))
    chap_a = chapter_repo.save(
        Chapter(
            project_id=proj_a.id,
            source_id=src_a.id,
            chapter_number=1,
            sequence_index=0,
            title="A Chapter",
            start_offset=0,
            end_offset=100,
            original_text="Text A",
        )
    )

    # Create Project B
    proj_b = proj_repo.save(Project(title="Project B"))
    src_b = source_repo.save(Source(project_id=proj_b.id, uri_or_path="/path/b.txt"))
    chap_b = chapter_repo.save(
        Chapter(
            project_id=proj_b.id,
            source_id=src_b.id,
            chapter_number=1,
            sequence_index=0,
            title="B Chapter",
            start_offset=0,
            end_offset=100,
            original_text="Text B",
        )
    )

    # Verify Project A query never returns Project B entities
    chaps_a = chapter_repo.list_by_project(proj_a.id)
    assert len(chaps_a) == 1
    assert chaps_a[0].title == "A Chapter"

    chaps_b = chapter_repo.list_by_project(proj_b.id)
    assert len(chaps_b) == 1
    assert chaps_b[0].title == "B Chapter"


def test_crash_recovery_job_interruption(tmp_path: Path):
    db_file = tmp_path / "test_crash.db"

    # Step 1: Create a job in RUNNING status and simulate application crash
    engine1 = DatabaseEngine(db_file)
    MigrationRunner(engine1).apply_migrations()
    proj = ProjectRepository(engine1).save(Project(title="Crash Test"))
    job_repo1 = JobRepository(engine1)

    running_job = job_repo1.save(
        Job(project_id=proj.id, job_type=JobType.GENERATE_TTS, status=JobStatus.RUNNING)
    )
    completed_job = job_repo1.save(
        Job(project_id=proj.id, job_type=JobType.IMPORT_SOURCE, status=JobStatus.COMPLETED)
    )
    engine1.close()

    # Step 2: Restart application (apply_migrations performs crash recovery)
    engine2 = DatabaseEngine(db_file)
    migrator2 = MigrationRunner(engine2)
    migrator2.apply_migrations()
    job_repo2 = JobRepository(engine2)

    # Completed job remains COMPLETED
    reloaded_completed = job_repo2.get_by_id(completed_job.id)
    assert reloaded_completed.status == JobStatus.COMPLETED

    # Stale RUNNING job becomes INTERRUPTED
    reloaded_running = job_repo2.get_by_id(running_job.id)
    assert reloaded_running.status == JobStatus.INTERRUPTED
    assert "terminated" in reloaded_running.error_message.lower()

    engine2.close()


def test_asset_registration_validation(test_db: DatabaseEngine, tmp_path: Path):
    proj_repo = ProjectRepository(test_db)
    asset_repo = AssetRepository(test_db)

    proj = proj_repo.save(Project(title="Asset Project"))

    # Valid non-empty file asset
    valid_file = tmp_path / "sample.mp3"
    valid_file.write_bytes(b"dummy_audio_bytes")

    asset = Asset(project_id=proj.id, asset_type=AssetType.AUDIO, path=str(valid_file))
    registered = asset_repo.register_asset(asset)

    assert registered.status == AssetStatus.VALIDATED
    assert registered.size_bytes == len(b"dummy_audio_bytes")
