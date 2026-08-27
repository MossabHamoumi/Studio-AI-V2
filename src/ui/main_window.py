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
from src.repositories.project_repo import ProjectRepository
from src.services.workspace_manager import WorkspaceManager
from src.ui.dashboard_view import DashboardView
from src.ui.projects_view import ProjectsView


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
        workspace_mgr: WorkspaceManager,
    ):
        super().__init__()
        self.settings = settings
        self.db_engine = db_engine
        self.project_repo = project_repo
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

        self.content_stack.addWidget(self.dashboard_view)
        self.content_stack.addWidget(self.projects_view)
        self.content_stack.addWidget(PlaceholderView("Create Wizard"))
        self.content_stack.addWidget(PlaceholderView("Workspace"))
        self.content_stack.addWidget(PlaceholderView("Production Orchestrator"))
        self.content_stack.addWidget(PlaceholderView("Asset Library"))
        self.content_stack.addWidget(PlaceholderView("Settings"))

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
