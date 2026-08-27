"""Projects View for real project creation, switching, and listing."""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.domain.models import Project, ProjectType
from src.repositories.project_repo import ProjectRepository
from src.services.workspace_manager import WorkspaceManager


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Project Title")
        layout.addRow("Project Title:", self.txt_title)

        self.cmb_type = QComboBox()
        for ptype in ProjectType:
            self.cmb_type.addItem(ptype.value)
        layout.addRow("Project Type:", self.cmb_type)

        btn_box = QHBoxLayout()
        self.btn_create = QPushButton("Create")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_create.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_create)
        btn_box.addWidget(self.btn_cancel)

        layout.addRow(btn_box)

    def get_data(self) -> tuple[str, ProjectType]:
        return self.txt_title.text().strip(), ProjectType(self.cmb_type.currentText())


class ProjectsView(QWidget):
    """Real project management view."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        workspace_mgr: WorkspaceManager,
        on_project_selected: Callable[[Project], None],
        parent=None,
    ):
        super().__init__(parent)
        self.project_repo = project_repo
        self.workspace_mgr = workspace_mgr
        self.on_project_selected = on_project_selected
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        title = QLabel("Projects")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_layout.addWidget(title)

        top_layout.addStretch()

        btn_new = QPushButton("+ New Project")
        btn_new.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 8px 16px; font-weight: bold; border-radius: 4px;"
        )
        btn_new.clicked.connect(self.handle_new_project)
        top_layout.addWidget(btn_new)

        layout.addLayout(top_layout)

        # Projects Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Type", "Status", "Updated At"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self.handle_row_double_click)
        layout.addWidget(self.table)

        self.load_projects()

    def load_projects(self):
        projects = self.project_repo.list_all()
        self.table.setRowCount(len(projects))
        self.projects_list = projects

        for idx, p in enumerate(projects):
            self.table.setItem(idx, 0, QTableWidgetItem(p.title))
            self.table.setItem(idx, 1, QTableWidgetItem(p.project_type.value))
            self.table.setItem(idx, 2, QTableWidgetItem(p.status.value))
            self.table.setItem(idx, 3, QTableWidgetItem(p.updated_at[:19]))

    def handle_new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            title, ptype = dialog.get_data()
            if not title:
                return
            project = Project(title=title, project_type=ptype)
            self.workspace_mgr.initialize_project_workspace(project)
            self.project_repo.save(project)
            self.load_projects()
            self.on_project_selected(project)

    def handle_row_double_click(self, row: int, col: int):
        if 0 <= row < len(self.projects_list):
            project = self.projects_list[row]
            self.on_project_selected(project)
