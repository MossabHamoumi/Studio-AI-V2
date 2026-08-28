"""Production Orchestrator View for PySide6 Desktop UI.

Displays render pipeline progress, stage logs, System Doctor health summary,
and QA report inspection.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.models import Project
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.services.render_pipeline import RenderPipeline
from src.services.system_doctor import SystemDoctor


class ProductionView(QWidget):
    """Production Orchestrator View."""

    def __init__(
        self,
        chapter_repo: ChapterRepository,
        asset_repo: AssetRepository,
        settings: AppSettings,
        parent=None,
    ):
        super().__init__(parent)
        self.chapter_repo = chapter_repo
        self.asset_repo = asset_repo
        self.settings = settings
        self.pipeline = RenderPipeline(settings, asset_repo)
        self.doctor = SystemDoctor(settings)

        self.active_project: Optional[Project] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Production Orchestrator")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Progress Box
        grp_prog = QGroupBox("Active Render Run")
        vbox_prog = QVBoxLayout(grp_prog)

        self.lbl_status = QLabel("Status: Idle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        btn_box = QHBoxLayout()
        btn_start_render = QPushButton("Start Production Render")
        btn_start_render.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        btn_start_render.clicked.connect(self.handle_start_render)

        btn_cancel_render = QPushButton("Cancel Render")
        btn_cancel_render.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 10px;")
        btn_cancel_render.clicked.connect(self.handle_cancel_render)

        btn_box.addWidget(btn_start_render)
        btn_box.addWidget(btn_cancel_render)

        vbox_prog.addWidget(self.lbl_status)
        vbox_prog.addWidget(self.progress_bar)
        vbox_prog.addLayout(btn_box)

        layout.addWidget(grp_prog)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Logs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        grp_logs = QGroupBox("Pipeline Execution Logs")
        vbox_logs = QVBoxLayout(grp_logs)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        vbox_logs.addWidget(self.txt_logs)
        left_layout.addWidget(grp_logs)

        splitter.addWidget(left_widget)

        # Right: System Doctor & QA Report
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        grp_doctor = QGroupBox("System Doctor Health Summary")
        vbox_doctor = QVBoxLayout(grp_doctor)
        self.txt_doctor = QTextEdit()
        self.txt_doctor.setReadOnly(True)
        vbox_doctor.addWidget(self.txt_doctor)
        right_layout.addWidget(grp_doctor)

        grp_qa = QGroupBox("Media QA Report")
        vbox_qa = QVBoxLayout(grp_qa)
        self.txt_qa = QTextEdit()
        self.txt_qa.setReadOnly(True)
        vbox_qa.addWidget(self.txt_qa)
        right_layout.addWidget(grp_qa)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        self.refresh_doctor_summary()

    def set_active_project(self, project: Project):
        self.active_project = project

    def refresh_doctor_summary(self):
        checks = self.doctor.run_foundation_checks()
        lines = []
        for cat, info in checks.items():
            status = info.get("status", "UNKNOWN")
            lines.append(f"[{status}] {cat.upper()}: {info}")
        self.txt_doctor.setPlainText("\n".join(lines))

    def handle_start_render(self):
        if not self.active_project:
            self.lbl_status.setText("Status: No active project selected")
            return

        self.lbl_status.setText("Status: Ready to render (Select chapter in Visual/Subtitle view)")
        self.txt_logs.append("Render pipeline ready. Complete stage orchestrator to be wired in Phase 8.")

    def handle_cancel_render(self):
        self.pipeline.cancel_render()
        self.lbl_status.setText("Status: CANCELLED")
        self.txt_logs.append("Render cancelled by user.")
