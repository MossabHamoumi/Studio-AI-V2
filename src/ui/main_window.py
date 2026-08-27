"""Main Window for Studio-AI desktop shell."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.database.engine import DatabaseEngine
from src.domain.models import Project
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.workspace_manager import WorkspaceManager
from src.ui.ai_view import AIView
from src.ui.dashboard_view import DashboardView
from src.ui.library_view import LibraryView
from src.ui.projects_view import ProjectsView
from src.ui.workspace_view import WorkspaceView


class PlaceholderView(QWidget):
    """Placeholder view for future phase modules."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"{name} Module\n(Planned for future rebuild phase)")
        lbl.setStyleSheet("font-size: 18px; color: #888888; text-align: center;")
        layout.addWidget(lbl)


class MainWindow(QMainWindow):
    """Studio-AI Main Desktop Window."""

    def __init__(
        self,
        settings: AppSettings,
        db_engine: DatabaseEngine,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        section_repo: SectionRepository,
        analysis_repo: AnalysisRepository,
        adaptation_repo: AdaptationRepository,
        workspace_mgr: WorkspaceManager,
    ):
        super().__init__()
        self.settings = settings
        self.db_engine = db_engine
        self.project_repo = project_repo
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.section_repo = section_repo
        self.analysis_repo = analysis_repo
        self.adaptation_repo = adaptation_repo
        self.workspace_mgr = workspace_mgr
        self.active_project: Optional[Project] = None

        self.setWindowTitle("Studio-AI Desktop Studio")
        self.resize(1100, 700)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar navigation
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet(
            "QListWidget { background-color: #1e1e1e; color: #dcdcdc; font-size: 14px; border: none; }"
            "QListWidget::item { padding: 12px; }"
            "QListWidget::item:selected { background-color: #0d47a1; color: white; }"
        )

        nav_items = [
            "Dashboard",
            "Projects",
            "Create",
            "Workspace",
            "AI Director",
            "Production",
            "Library",
            "Settings",
        ]
        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        main_layout.addWidget(self.nav_list)

        # Content Stack
        self.content_stack = QStackedWidget()

        self.dashboard_view = DashboardView(self.project_repo)
        self.projects_view = ProjectsView(
            self.project_repo, self.workspace_mgr, self.on_project_activated
        )
        self.workspace_view = WorkspaceView(
            self.source_repo, self.chapter_repo, self.section_repo
        )
        self.ai_view = AIView(
            self.analysis_repo, self.adaptation_repo, self.chapter_repo, self.settings
        )
        self.library_view = LibraryView(self.settings)

        self.content_stack.addWidget(self.dashboard_view)        # 0
        self.content_stack.addWidget(self.projects_view)         # 1
        self.content_stack.addWidget(PlaceholderView("Create Wizard")) # 2
        self.content_stack.addWidget(self.workspace_view)        # 3
        self.content_stack.addWidget(self.ai_view)               # 4
        self.content_stack.addWidget(PlaceholderView("Production Orchestrator")) # 5
        self.content_stack.addWidget(self.library_view)          # 6
        self.content_stack.addWidget(PlaceholderView("Settings"))      # 7

        # Right Panel (Stack + Active Project Header)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.lbl_active_project = QLabel("Active Project: None")
        self.lbl_active_project.setStyleSheet(
            "font-weight: bold; background-color: #333; color: white; padding: 6px 12px;"
        )
        right_layout.addWidget(self.lbl_active_project)
        right_layout.addWidget(self.content_stack)

        main_layout.addWidget(right_panel)

        self.setCentralWidget(main_widget)

        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def on_project_activated(self, project: Project):
        """Handle project selection/activation."""
        self.active_project = project
        self.lbl_active_project.setText(
            f"Active Project: {project.title} ({project.project_type.value})"
        )
        self.dashboard_view.refresh()
        self.workspace_view.set_active_project(project)
        self.ai_view.set_active_project(project)
