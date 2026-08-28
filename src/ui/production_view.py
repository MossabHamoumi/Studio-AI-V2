"""Production Orchestrator View for PySide6 Desktop UI.

Displays render pipeline progress, stage logs, System Doctor health summary,
chapter selection controls, and QA report inspection.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
from src.domain.models import Chapter, Project
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.job_repo import JobRepository
from src.repositories.production_run_repo import ProductionRunRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.source_repo import SourceRepository
from src.services.production_orchestrator import ProductionOrchestrator
from src.services.system_doctor import SystemDoctor


class ProductionView(QWidget):
    """Production Orchestrator View."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        analysis_repo: AnalysisRepository,
        adaptation_repo: AdaptationRepository,
        asset_repo: AssetRepository,
        job_repo: JobRepository,
        production_run_repo: ProductionRunRepository,
        settings: AppSettings,
        parent=None,
    ):
        super().__init__(parent)
        self.project_repo = project_repo
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.analysis_repo = analysis_repo
        self.adaptation_repo = adaptation_repo
        self.asset_repo = asset_repo
        self.job_repo = job_repo
        self.run_repo = production_run_repo
        self.settings = settings

        self.orchestrator = ProductionOrchestrator(
            settings,
            project_repo,
            source_repo,
            chapter_repo,
            analysis_repo,
            adaptation_repo,
            asset_repo,
            job_repo,
            production_run_repo,
        )
        self.doctor = SystemDoctor(settings)

        self.active_project: Optional[Project] = None
        self.chapters_list = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Production Orchestrator")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Selection Controls Box
        grp_controls = QGroupBox("Production Run Target Selection")
        form_controls = QFormLayout(grp_controls)

        self.cmb_scope = QComboBox()
        self.cmb_scope.addItem("Selected Chapter Only")
        self.cmb_scope.addItem("Entire Novel (All Chapters)")
        self.cmb_scope.currentIndexChanged.connect(self.handle_scope_changed)

        self.cmb_chapters = QComboBox()

        form_controls.addRow("Production Scope:", self.cmb_scope)
        form_controls.addRow("Target Chapter:", self.cmb_chapters)
        layout.addWidget(grp_controls)

        # Progress Box
        grp_prog = QGroupBox("Active Render Run")
        vbox_prog = QVBoxLayout(grp_prog)

        self.lbl_status = QLabel("Status: Idle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        btn_box = QHBoxLayout()
        btn_start_render = QPushButton("Start Production Run")
        btn_start_render.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        btn_start_render.clicked.connect(self.handle_start_render)

        btn_cancel_render = QPushButton("Cancel Production Run")
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
        self.reload_chapters()

    def reload_chapters(self):
        if not self.active_project:
            return

        self.chapters_list = self.chapter_repo.list_by_project(self.active_project.id)
        self.cmb_chapters.clear()
        for idx, ch in enumerate(self.chapters_list):
            self.cmb_chapters.addItem(f"Chapter #{ch.sequence_index + 1}: {ch.title}", ch.id)

    def handle_scope_changed(self, index: int):
        # Disable chapter selector if "Entire Novel" selected
        self.cmb_chapters.setEnabled(index == 0)

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

        if not self.chapters_list:
            self.lbl_status.setText("Status: Project has no chapters")
            return

        is_entire_novel = self.cmb_scope.currentIndex() == 1

        self.lbl_status.setText("Status: Starting Production Run...")
        self.txt_logs.append(f"Initiating Production Run for project '{self.active_project.title}'...")

        def _on_progress(stage: str, prog: float):
            self.lbl_status.setText(f"Status: Stage {stage} ({int(prog * 100)}%)")
            self.progress_bar.setValue(int(prog * 100))
            self.txt_logs.append(f"Stage {stage}: {int(prog * 100)}%")

        try:
            if is_entire_novel:
                self.orchestrator.run_novel_production(self.active_project.id)
                self.lbl_status.setText("Status: ENTIRE NOVEL COMPLETED (QA PASS)")
                self.txt_logs.append("Entire novel production run COMPLETED across all chapters.")
            else:
                selected_chapter_id = self.cmb_chapters.currentData()
                if not selected_chapter_id and self.chapters_list:
                    selected_chapter_id = self.chapters_list[0].id

                run, out_file, qa_report = self.orchestrator.run_chapter_production(
                    project_id=self.active_project.id,
                    chapter_id=selected_chapter_id,
                    progress_callback=_on_progress,
                )
                self.lbl_status.setText("Status: COMPLETED (QA PASS)")
                self.txt_logs.append(f"Production Run COMPLETED. Output: {out_file}")
                self.txt_qa.setPlainText(f"QA PASS: {out_file.name}\nResolution: {qa_report.measured_width}x{qa_report.measured_height}\nDuration: {qa_report.measured_duration_sec:.2f}s")
        except Exception as e:
            self.lbl_status.setText(f"Status: FAILED ({e})")
            self.txt_logs.append(f"Production Run FAILED: {e}")

    def handle_cancel_render(self):
        self.orchestrator.render_pipeline.cancel_render()
        self.lbl_status.setText("Status: CANCELLED")
        self.txt_logs.append("Render cancelled by user.")
