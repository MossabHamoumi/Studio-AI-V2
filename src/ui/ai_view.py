"""AI View for PySide6 Desktop UI.

Manages AI mode selection, story analysis execution, timeout retry/fallback banners,
and adaptation review controls.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.ai_models import AIMode, AIStatus, AdaptationStatus, AnalysisType
from src.domain.models import Chapter, Project
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.chapter_repo import ChapterRepository
from src.services.ai_director import AIDirector


class AIView(QWidget):
    """AI Studio View for story analysis and adaptation review."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        adaptation_repo: AdaptationRepository,
        chapter_repo: ChapterRepository,
        settings: AppSettings,
        parent=None,
    ):
        super().__init__(parent)
        self.analysis_repo = analysis_repo
        self.adaptation_repo = adaptation_repo
        self.chapter_repo = chapter_repo
        self.settings = settings
        self.director = AIDirector(analysis_repo, adaptation_repo, settings)

        self.active_project: Optional[Project] = None
        self.active_chapter: Optional[Chapter] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header controls
        top_layout = QHBoxLayout()
        title = QLabel("Local AI Director")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        top_layout.addWidget(title)

        top_layout.addStretch()

        top_layout.addWidget(QLabel("AI Mode:"))
        self.cmb_mode = QComboBox()
        for mode in AIMode:
            self.cmb_mode.addItem(mode.value)
        top_layout.addWidget(self.cmb_mode)

        layout.addLayout(top_layout)

        # Timeout Banner (Hidden by default)
        self.banner = QWidget()
        self.banner.setStyleSheet("background-color: #d32f2f; color: white; padding: 10px; border-radius: 6px;")
        banner_layout = QHBoxLayout(self.banner)
        self.lbl_banner_msg = QLabel("AI TIMEOUT: Ollama server timed out.")
        self.lbl_banner_msg.setStyleSheet("font-weight: bold; font-size: 14px;")
        btn_retry = QPushButton("RETRY")
        btn_retry.clicked.connect(self.handle_run_analysis)
        btn_local = QPushButton("CONTINUE LOCALLY")
        btn_local.clicked.connect(self.handle_continue_locally)

        banner_layout.addWidget(self.lbl_banner_msg)
        banner_layout.addStretch()
        banner_layout.addWidget(btn_retry)
        banner_layout.addWidget(btn_local)
        self.banner.hide()
        layout.addWidget(self.banner)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Chapter List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Select Chapter:"))

        self.tbl_chapters = QTableWidget()
        self.tbl_chapters.setColumnCount(2)
        self.tbl_chapters.setHorizontalHeaderLabels(["Seq", "Title"])
        self.tbl_chapters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_chapters.cellClicked.connect(self.handle_chapter_selected)
        left_layout.addWidget(self.tbl_chapters)

        btn_run_analysis = QPushButton("Run AI Analysis")
        btn_run_analysis.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold; padding: 8px;")
        btn_run_analysis.clicked.connect(self.handle_run_analysis)
        left_layout.addWidget(btn_run_analysis)

        btn_run_adaptation = QPushButton("Run Script Adaptation")
        btn_run_adaptation.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 8px;")
        btn_run_adaptation.clicked.connect(self.handle_run_adaptation)
        left_layout.addWidget(btn_run_adaptation)

        splitter.addWidget(left_widget)

        # Right: Analysis & Adaptation Details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Analysis Card
        grp_analysis = QGroupBox("Structured Story Analysis")
        form_analysis = QFormLayout(grp_analysis)

        self.lbl_analysis_type = QLabel("None")
        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_characters = QLineEdit()
        self.txt_characters.setReadOnly(True)
        self.lbl_tone_mood = QLabel("Tone: - | Mood: -")

        form_analysis.addRow("Result Type:", self.lbl_analysis_type)
        form_analysis.addRow("Summary:", self.txt_summary)
        form_analysis.addRow("Characters:", self.txt_characters)
        form_analysis.addRow("Tone & Mood:", self.lbl_tone_mood)
        right_layout.addWidget(grp_analysis)

        # Adaptation Card
        grp_adapt = QGroupBox("Script Adaptation Review")
        vbox_adapt = QVBoxLayout(grp_adapt)

        self.lbl_adapt_status = QLabel("Status: NONE")
        self.txt_adapted_script = QTextEdit()

        btn_box = QHBoxLayout()
        btn_accept = QPushButton("ACCEPT")
        btn_accept.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_accept.clicked.connect(self.handle_accept_adaptation)

        btn_reject = QPushButton("REJECT")
        btn_reject.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
        btn_reject.clicked.connect(self.handle_reject_adaptation)

        btn_regen = QPushButton("REGENERATE")
        btn_regen.clicked.connect(self.handle_run_adaptation)

        btn_box.addWidget(btn_accept)
        btn_box.addWidget(btn_reject)
        btn_box.addWidget(btn_regen)

        vbox_adapt.addWidget(self.lbl_adapt_status)
        vbox_adapt.addWidget(self.txt_adapted_script)
        vbox_adapt.addLayout(btn_box)
        right_layout.addWidget(grp_adapt)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

    def set_active_project(self, project: Project):
        self.active_project = project
        self.reload_chapters()

    def reload_chapters(self):
        if not self.active_project:
            return

        chapters = self.chapter_repo.list_by_project(self.active_project.id)
        self.chapters_list = chapters
        self.tbl_chapters.setRowCount(len(chapters))

        for idx, c in enumerate(chapters):
            self.tbl_chapters.setItem(idx, 0, QTableWidgetItem(str(c.sequence_index)))
            self.tbl_chapters.setItem(idx, 1, QTableWidgetItem(c.title))

        if chapters:
            self.handle_chapter_selected(0, 0)

    def handle_chapter_selected(self, row: int, col: int):
        if 0 <= row < len(self.chapters_list):
            self.active_chapter = self.chapters_list[row]
            self.refresh_chapter_details()

    def refresh_chapter_details(self):
        if not self.active_chapter:
            return

        analysis = self.analysis_repo.get_by_chapter(self.active_chapter.id)
        if analysis:
            self.lbl_analysis_type.setText(f"{analysis.analysis_type.value} ({analysis.model_used})")
            self.txt_summary.setPlainText(analysis.summary)
            self.txt_characters.setText(", ".join(analysis.characters))
            self.lbl_tone_mood.setText(f"Tone: {analysis.tone} | Mood: {analysis.mood}")
        else:
            self.lbl_analysis_type.setText("None")
            self.txt_summary.clear()
            self.txt_characters.clear()
            self.lbl_tone_mood.setText("Tone: - | Mood: -")

        adaptation = self.adaptation_repo.get_by_chapter(self.active_chapter.id)
        if adaptation:
            self.lbl_adapt_status.setText(f"Status: {adaptation.status.value}")
            self.txt_adapted_script.setPlainText(adaptation.adapted_text)
        else:
            self.lbl_adapt_status.setText("Status: NONE")
            self.txt_adapted_script.clear()

    def handle_run_analysis(self):
        if not self.active_project or not self.active_chapter:
            return

        self.banner.hide()
        mode = AIMode(self.cmb_mode.currentText())

        analysis, status = self.director.analyze_chapter(
            project_id=self.active_project.id,
            chapter_id=self.active_chapter.id,
            chapter_text=self.active_chapter.cleaned_text or self.active_chapter.original_text,
            source_text_hash=self.active_chapter.content_hash,
            mode=mode,
        )

        if status == AIStatus.TIMEOUT:
            self.banner.show()

        self.refresh_chapter_details()

    def handle_continue_locally(self):
        if not self.active_project or not self.active_chapter:
            return

        self.banner.hide()
        analysis, _ = self.director.analyze_chapter(
            project_id=self.active_project.id,
            chapter_id=self.active_chapter.id,
            chapter_text=self.active_chapter.cleaned_text or self.active_chapter.original_text,
            source_text_hash=self.active_chapter.content_hash,
            mode=AIMode.LOCAL_ONLY,
        )
        self.refresh_chapter_details()

    def handle_run_adaptation(self):
        if not self.active_project or not self.active_chapter:
            return

        mode = AIMode(self.cmb_mode.currentText())
        try:
            adaptation, status = self.director.adapt_chapter_script(
                project_id=self.active_project.id,
                chapter_id=self.active_chapter.id,
                chapter_text=self.active_chapter.cleaned_text or self.active_chapter.original_text,
                source_text_hash=self.active_chapter.content_hash,
                mode=mode,
            )
        except Exception:
            pass

        self.refresh_chapter_details()

    def handle_accept_adaptation(self):
        if not self.active_chapter:
            return
        adapt = self.adaptation_repo.get_by_chapter(self.active_chapter.id)
        if adapt:
            self.director.update_adaptation_status(adapt.id, AdaptationStatus.ACCEPTED)
            self.refresh_chapter_details()

    def handle_reject_adaptation(self):
        if not self.active_chapter:
            return
        adapt = self.adaptation_repo.get_by_chapter(self.active_chapter.id)
        if adapt:
            self.director.update_adaptation_status(adapt.id, AdaptationStatus.REJECTED)
            self.refresh_chapter_details()
