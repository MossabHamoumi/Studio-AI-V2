"""Main entry point for Studio-AI desktop application.

Handles Python environment diagnostics, --doctor CLI argument execution,
and PySide6 GUI launching with actionable error messages if dependencies are missing.
"""

import sys
from pathlib import Path
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.database.migrations import MigrationRunner
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.system_doctor import SystemDoctor
from src.services.workspace_manager import WorkspaceManager
from src.utilities.logging import setup_logging


def print_environment_diagnostics():
    """Print Python executable and virtual environment diagnostics on startup."""
    is_venv = sys.prefix != sys.base_prefix
    venv_status = f"ACTIVE ({sys.prefix})" if is_venv else "NOT FOUND / GLOBAL"

    print("=" * 60)
    print("            STUDIO-AI BOOTSTRAP ENVIRONMENT")
    print("=" * 60)
    print(f"  Python Executable : {sys.executable}")
    print(f"  Python Version    : {sys.version.split()[0]}")
    print(f"  Virtual Env       : {venv_status}")
    print("=" * 60)


def main():
    """Studio-AI entry point."""
    print_environment_diagnostics()

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

    # Launch PySide6 Desktop GUI (Lazy Import)
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
    except ModuleNotFoundError as e:
        print("\n[CRITICAL ERROR] PySide6 GUI dependency is missing!")
        print(f"  Current Python Executable : {sys.executable}")
        print(f"  Error Details            : {e}")
        print("\n  To fix this issue, please run:")
        print("    .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n")
        engine.close()
        sys.exit(1)

    app = QApplication(sys.argv)
    project_repo = ProjectRepository(engine)
    source_repo = SourceRepository(engine)
    chapter_repo = ChapterRepository(engine)
    section_repo = SectionRepository(engine)
    analysis_repo = AnalysisRepository(engine)
    adaptation_repo = AdaptationRepository(engine)
    asset_repo = AssetRepository(engine)
    job_repo = JobRepository(engine)
    run_repo = ProductionRunRepository(engine)

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
        asset_repo,
        job_repo,
        run_repo,
        workspace_mgr,
    )
    window.show()

    ret_code = app.exec()
    engine.close()
    sys.exit(ret_code)


if __name__ == "__main__":
    main()
