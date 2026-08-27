"""Unit tests for workspace management, path handling, and idempotency."""

from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.domain.models import JobType, Project, ProjectType
from src.services.idempotency import compute_job_signature
from src.services.workspace_manager import WorkspaceManager


def test_workspace_manager_unicode_spaces_onedrive_path(tmp_path: Path):
    # Test path with spaces, Unicode, and OneDrive structure
    complex_dir = tmp_path / "OneDrive - Personal" / "Studio AI Projects" / "Proyecto Stories 🚀"
    settings = AppSettings(workspace_dir=complex_dir)
    ws_mgr = WorkspaceManager(settings)

    project = Project(title="OneDrive Unicode Story 🚀", project_type=ProjectType.CUSTOM)
    pdir = ws_mgr.initialize_project_workspace(project)

    assert pdir.exists()
    assert (pdir / "project.json").exists()
    assert "OneDrive - Personal" in str(pdir)


def test_compute_job_signature_idempotency():
    sig1 = compute_job_signature(
        project_id="proj-123",
        job_type=JobType.GENERATE_TTS,
        input_hash="hash_abc123",
        chapter_id="chap-1",
    )

    sig2 = compute_job_signature(
        project_id="proj-123",
        job_type=JobType.GENERATE_TTS,
        input_hash="hash_abc123",
        chapter_id="chap-1",
    )

    # Identical inputs yield identical work signature
    assert sig1 == sig2
    assert len(sig1) == 64  # SHA-256 hex digest length
