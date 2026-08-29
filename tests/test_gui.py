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
from src.domain.session_context import SessionContext
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.production_orchestrator import ProductionOrchestrator
from src.services.workspace_manager import WorkspaceManager
from src.ui.ai_view import AIView
from src.ui.create_wizard_view import CreateWizardView
from src.ui.dashboard_view import DashboardView
from src.ui.library_view import LibraryView
from src.ui.main_window import MainWindow
from src.ui.production_view import ProductionView
from src.ui.projects_view import ProjectsView
from src.ui.subtitle_view import SubtitleView
from src.ui.visual_view import VisualView
from src.ui.workspace_view import WorkspaceView


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
    asset_repo = AssetRepository(engine)
    job_repo = JobRepository(engine)
    run_repo = ProductionRunRepository(engine)

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
        asset_repo,
        job_repo,
        run_repo,
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


def test_all_views_individual_construction(qapp, tmp_path: Path):
    """Smoke test ensuring every view constructs cleanly with keyword parameters without unexpected argument errors."""
    settings = AppSettings(workspace_dir=tmp_path)
    engine = DatabaseEngine(settings.db_path)
    MigrationRunner(engine).apply_migrations()

    proj_repo = ProjectRepository(engine)
    source_repo = SourceRepository(engine)
    chapter_repo = ChapterRepository(engine)
    section_repo = SectionRepository(engine)
    analysis_repo = AnalysisRepository(engine)
    adaptation_repo = AdaptationRepository(engine)
    asset_repo = AssetRepository(engine)
    job_repo = JobRepository(engine)
    run_repo = ProductionRunRepository(engine)
    ws_mgr = WorkspaceManager(settings)
    session_ctx = SessionContext()

    orchestrator = ProductionOrchestrator(
        settings=settings,
        project_repo=proj_repo,
        source_repo=source_repo,
        chapter_repo=chapter_repo,
        analysis_repo=analysis_repo,
        adaptation_repo=adaptation_repo,
        asset_repo=asset_repo,
        job_repo=job_repo,
        production_run_repo=run_repo,
    )

    # 1. DashboardView
    v0 = DashboardView(project_repo=proj_repo)
    assert v0 is not None

    # 2. ProjectsView
    v1 = ProjectsView(
        project_repo=proj_repo,
        workspace_mgr=ws_mgr,
        on_project_selected=lambda p: None,
    )
    assert v1 is not None

    # 3. CreateWizardView
    v2 = CreateWizardView(
        session_ctx=session_ctx,
        project_repo=proj_repo,
        source_repo=source_repo,
        chapter_repo=chapter_repo,
        section_repo=section_repo,
        workspace_mgr=ws_mgr,
        orchestrator=orchestrator,
        settings=settings,
    )
    assert v2 is not None

    # 4. WorkspaceView
    v3 = WorkspaceView(
        source_repo=source_repo,
        chapter_repo=chapter_repo,
        section_repo=section_repo,
        session_ctx=session_ctx,
    )
    assert v3 is not None

    # 5. AIView
    v4 = AIView(
        analysis_repo=analysis_repo,
        adaptation_repo=adaptation_repo,
        chapter_repo=chapter_repo,
        settings=settings,
    )
    assert v4 is not None

    # 6. SubtitleView
    v5 = SubtitleView(
        chapter_repo=chapter_repo,
        settings=settings,
    )
    assert v5 is not None

    # 7. VisualView
    v6 = VisualView(
        asset_repo=asset_repo,
        chapter_repo=chapter_repo,
        settings=settings,
    )
    assert v6 is not None

    # 8. ProductionView
    v7 = ProductionView(
        project_repo=proj_repo,
        source_repo=source_repo,
        chapter_repo=chapter_repo,
        analysis_repo=analysis_repo,
        adaptation_repo=adaptation_repo,
        asset_repo=asset_repo,
        job_repo=job_repo,
        production_run_repo=run_repo,
        settings=settings,
    )
    assert v7 is not None

    # 9. LibraryView
    v8 = LibraryView(settings=settings)
    assert v8 is not None

    engine.close()


def test_startup_dependency_graph_regression(tmp_path: Path):
    """Regression test ensuring MainWindow and ProductionOrchestrator receive AppSettings properly."""
    settings = AppSettings(workspace_dir=tmp_path)
    engine = DatabaseEngine(settings.db_path)
    MigrationRunner(engine).apply_migrations()

    proj_repo = ProjectRepository(engine)
    source_repo = SourceRepository(engine)
    chapter_repo = ChapterRepository(engine)
    section_repo = SectionRepository(engine)
    analysis_repo = AnalysisRepository(engine)
    adaptation_repo = AdaptationRepository(engine)
    asset_repo = AssetRepository(engine)
    job_repo = JobRepository(engine)
    run_repo = ProductionRunRepository(engine)

    # Verify ProductionOrchestrator throws TypeError if settings is accidentally a ProjectRepository
    with pytest.raises(TypeError, match="must be an AppSettings instance"):
        ProductionOrchestrator(
            settings=proj_repo,  # Wrong object passed as settings!
            project_repo=proj_repo,
            source_repo=source_repo,
            chapter_repo=chapter_repo,
            analysis_repo=analysis_repo,
            adaptation_repo=adaptation_repo,
            asset_repo=asset_repo,
            job_repo=job_repo,
            production_run_repo=run_repo,
        )

    # Verify valid ProductionOrchestrator construction with AppSettings
    orchestrator = ProductionOrchestrator(
        settings=settings,
        project_repo=proj_repo,
        source_repo=source_repo,
        chapter_repo=chapter_repo,
        analysis_repo=analysis_repo,
        adaptation_repo=adaptation_repo,
        asset_repo=asset_repo,
        job_repo=job_repo,
        production_run_repo=run_repo,
    )
    assert orchestrator.settings == settings
    assert hasattr(orchestrator.settings, "logs_dir")
    engine.close()
