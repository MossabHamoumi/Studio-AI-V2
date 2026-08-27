"""Main entry point for Studio-AI desktop application."""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.system_doctor import SystemDoctor
from src.services.workspace_manager import WorkspaceManager
from src.ui.main_window import MainWindow
from src.utilities.logging import setup_logging


def main():
    """Studio-AI entry point."""
    settings = AppSettings()
    setup_logging(settings.app_log_path)

    # Database Initialization & Migration
    engine = DatabaseEngine(settings.db_path)
    migrator = MigrationRunner(engine)
    migrator.apply_migrations()

    # CLI Arguments Check
    if "--doctor" in sys.argv:
        doctor = SystemDoctor(settings)
        success = doctor.print_doctor_report()
        engine.close()
        sys.exit(0 if success else 1)

    # Launch PySide6 Desktop GUI
    app = QApplication(sys.argv)
    project_repo = ProjectRepository(engine)
    source_repo = SourceRepository(engine)
    chapter_repo = ChapterRepository(engine)
    section_repo = SectionRepository(engine)
    analysis_repo = AnalysisRepository(engine)
    adaptation_repo = AdaptationRepository(engine)

    workspace_mgr = WorkspaceManager(settings)

    window = MainWindow(
        settings,
        engine,
        project_repo,
        source_repo,
        chapter_repo,
        section_repo,
        analysis_repo,
        adaptation_repo,
        workspace_mgr,
    )
    window.show()

    ret_code = app.exec()
    engine.close()
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
