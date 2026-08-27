"""Unit tests for core domain models."""

import pytest
from src.domain.models import (
    Asset,
    AssetType,
    Chapter,
    Job,
    JobStatus,
    JobType,
    ProductionRun,
    Project,
    ProjectType,
    Section,
    Source,
    SourceType,
)


def test_project_model_defaults():
    project = Project(title="Test Novel", project_type=ProjectType.NOVEL)
    assert project.id is not None
    assert len(project.id) == 36  # UUID v4 string length
    assert project.title == "Test Novel"
    assert project.project_type == ProjectType.NOVEL


def test_chapter_sequence_index_isolation():
    chapter = Chapter(
        project_id="proj-1",
        source_id="src-1",
        chapter_number=1,
        sequence_index=0,
        title="Prologue",
        start_offset=0,
        end_offset=500,
        original_text="Once upon a time...",
    )
    assert chapter.chapter_number == 1
    assert chapter.sequence_index == 0


def test_job_model_initial_status():
    job = Job(project_id="proj-1", job_type=JobType.IMPORT_SOURCE)
    assert job.status == JobStatus.QUEUED
    assert job.progress == 0.0
