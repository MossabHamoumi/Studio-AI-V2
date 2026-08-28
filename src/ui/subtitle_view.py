"""Subtitle View for PySide6 Desktop UI.

Manages Subtitle ON/OFF toggles, ASS style profile selection, vertical alignment,
subtitle preview, and ASS/SRT file export.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.models import Chapter, Project
from src.domain.subtitle_models import SubtitleStyleProfile
from src.repositories.chapter_repo import ChapterRepository
from src.services.narration_engine import NarrationEngine
from src.services.subtitle_engine import SubtitleEngine


class SubtitleView(QWidget):
    """Subtitle Studio View for subtitle generation, alignment, and preview."""

    def __init__(
        self,
        chapter_repo: ChapterRepository,
        settings: AppSettings,
        parent=None,
    ):
        super().__init__(parent)
        self.chapter_repo = chapter_repo
        self.settings = settings
        self.subtitle_engine = SubtitleEngine(settings)
        self.narration_engine = NarrationEngine(settings)

        self.active_project: Optional[Project] = None
        self.active_chapter: Optional[Chapter] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Audio-Driven Subtitle Studio")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Settings Box
        grp_settings = QGroupBox("Subtitle Preferences")
        form_settings = QFormLayout(grp_settings)

        self.chk_enabled = QCheckBox("Enable Subtitles in Production")
        self.chk_enabled.setChecked(True)

        self.cmb_style = QComboBox()
        for style in SubtitleStyleProfile:
            self.cmb_style.addItem(style.value)

        self.cmb_anchor = QComboBox()
        self.cmb_anchor.addItem(r"\an5 (Center-Center - Reel Default)")
        self.cmb_anchor.addItem(r"\an2 (Bottom-Center)")
        self.cmb_anchor.addItem(r"\an8 (Top-Center)")

        form_settings.addRow(self.chk_enabled)
        form_settings.addRow("Style Profile:", self.cmb_style)
        form_settings.addRow("Vertical Anchor Alignment:", self.cmb_anchor)

        layout.addWidget(grp_settings)

        # Splitter (Left: Chapters, Right: Preview)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Chapter Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Select Chapter:"))

        self.tbl_chapters = QTableWidget()
        self.tbl_chapters.setColumnCount(2)
        self.tbl_chapters.setHorizontalHeaderLabels(["Seq", "Title"])
        self.tbl_chapters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_chapters.cellClicked.connect(self.handle_chapter_selected)
        left_layout.addWidget(self.tbl_chapters)

        btn_generate = QPushButton("Generate ASS & SRT Subtitles")
        btn_generate.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold; padding: 10px;")
        btn_generate.clicked.connect(self.handle_generate_subtitles)
        left_layout.addWidget(btn_generate)

        splitter.addWidget(left_widget)

        # Right: Subtitle Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        grp_preview = QGroupBox("Generated Subtitle Preview")
        vbox_preview = QVBoxLayout(grp_preview)

        self.lbl_status = QLabel("Status: Ready")
        self.txt_ass_preview = QTextEdit()
        self.txt_ass_preview.setReadOnly(True)

        vbox_preview.addWidget(self.lbl_status)
        vbox_preview.addWidget(self.txt_ass_preview)

        right_layout.addWidget(grp_preview)
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

    def handle_generate_subtitles(self):
        if not self.active_project or not self.active_chapter:
            return

        style_profile = SubtitleStyleProfile(self.cmb_style.currentText())

        try:
            # 1. Generate audio timeline
            timeline = self.narration_engine.generate_narration_timeline(
                project_id=self.active_project.id,
                chapter_id=self.active_chapter.id,
                text=self.active_chapter.cleaned_text or self.active_chapter.original_text,
            )

            # 2. Generate ASS and SRT subtitles from timeline
            ass_path, srt_path, val_res = self.subtitle_engine.generate_subtitles_from_audio_timeline(
                timeline=timeline,
                style_profile=style_profile,
            )

            self.lbl_status.setText(
                f"✓ Subtitles Validated ({val_res.total_events} events) | ASS: {ass_path.name}"
            )
            self.lbl_status.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.txt_ass_preview.setPlainText(ass_path.read_text(encoding="utf-8"))

        except Exception as e:
            self.lbl_status.setText(f"✗ Subtitle Generation Failed: {e}")
            self.lbl_status.setStyleSheet("color: #f44336; font-weight: bold;")
