"""GUI Integration tests for PySide6 MainWindow and Project creation."""

import os
from pathlib import Path
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.domain.models import Project, ProjectType
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.workspace_manager import WorkspaceManager
from src.ui.main_window import MainWindow


@pytest.fixture
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_launch_and_project_activation(qapp, tmp_path: Path):
    settings = AppSettings(workspace_dir=tmp_path)
    engine = DatabaseEngine(settings.db_path)
    MigrationRunner(engine).apply_migrations()
    proj_repo = ProjectRepository(engine)
    source_repo = SourceRepository(engine)
    chapter_repo = ChapterRepository(engine)
    section_repo = SectionRepository(engine)
    analysis_repo = AnalysisRepository(engine)
    adaptation_repo = AdaptationRepository(engine)

    ws_mgr = WorkspaceManager(settings)

    # Pre-create project
    project = proj_repo.save(Project(title="GUI Project", project_type=ProjectType.NOVEL))

    window = MainWindow(
        settings,
        engine,
        proj_repo,
        source_repo,
        chapter_repo,
        section_repo,
        analysis_repo,
        adaptation_repo,
        ws_mgr,
    )
    window.show()

    # Activate project
    window.on_project_activated(project)

    assert window.active_project is not None
    assert window.active_project.id == project.id
    assert "GUI Project" in window.lbl_active_project.text()

    window.close()
    window.deleteLater()
    QCoreApplication.processEvents()
    engine.close()
