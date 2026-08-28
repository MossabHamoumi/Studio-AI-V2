"""Content Workspace View for PySide6.

Displays imported sources, text statistics, chapter structure, original vs cleaned text,
manual edits, and stage navigation controls.
"""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
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
from src.domain.models import Chapter, Project, Source
from src.domain.session_context import SessionContext
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.content_engine import ContentEngine


class WorkspaceView(QWidget):
    """Content Workspace View for managing story text, chapters, and cleaning."""

    def __init__(

        self,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        section_repo: SectionRepository,
        session_ctx: SessionContext,
        on_navigate_stage: Optional[Callable[[int], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.section_repo = section_repo
        self.session_ctx = session_ctx
        self.on_navigate_stage = on_navigate_stage

        self.content_engine = ContentEngine(source_repo, chapter_repo, section_repo)

        self.active_project: Optional[Project] = None
        self.active_source: Optional[Source] = None
        self.active_chapter: Optional[Chapter] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header controls
        header_layout = QHBoxLayout()
        title = QLabel("Content Workspace")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_import = QPushButton("Import TXT File")
        btn_import.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;"
        )
        btn_import.clicked.connect(self.handle_import_file)
        header_layout.addWidget(btn_import)

        layout.addLayout(header_layout)

        # Main splitter (Left: Chapter List & Stats, Right: Text Viewers & Manual Overrides)
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.lbl_stats = QLabel("No source loaded.")
        self.lbl_stats.setStyleSheet("color: #aaa; padding: 6px; background-color: #2a2a2a;")
        left_layout.addWidget(self.lbl_stats)

        self.tbl_chapters = QTableWidget()
        self.tbl_chapters.setColumnCount(3)
        self.tbl_chapters.setHorizontalHeaderLabels(["Seq", "Ch #", "Title"])
        self.tbl_chapters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_chapters.cellClicked.connect(self.handle_chapter_selected)
        left_layout.addWidget(self.tbl_chapters)

        splitter.addWidget(left_widget)

        # Right Panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Manual Overrides Form
        edit_group = QGroupBox("Manual Chapter Overrides")
        edit_form = QFormLayout(edit_group)

        self.txt_edit_cnum = QLineEdit()
        self.txt_edit_title = QLineEdit()
        btn_save_override = QPushButton("Save Chapter Overrides")
        btn_save_override.clicked.connect(self.handle_save_override)

        edit_form.addRow("Chapter Number:", self.txt_edit_cnum)
        edit_form.addRow("Chapter Title:", self.txt_edit_title)
        edit_form.addRow(btn_save_override)
        right_layout.addWidget(edit_group)

        # Text Viewers (Original vs Cleaned)
        text_splitter = QSplitter(Qt.Vertical)

        orig_box = QGroupBox("Original Text (Immutable)")
        orig_layout = QVBoxLayout(orig_box)
        self.txt_original = QTextEdit()
        self.txt_original.setReadOnly(True)
        orig_layout.addWidget(self.txt_original)
        text_splitter.addWidget(orig_box)

        clean_box = QGroupBox("Cleaned Text")
        clean_layout = QVBoxLayout(clean_box)
        self.txt_cleaned = QTextEdit()
        clean_layout.addWidget(self.txt_cleaned)
        text_splitter.addWidget(clean_box)

        right_layout.addWidget(text_splitter)

        # Stage Navigation Button [ CONTINUE TO AI DIRECTOR ]
        btn_next_stage = QPushButton("CONTINUE TO AI DIRECTOR →")
        btn_next_stage.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        btn_next_stage.clicked.connect(self.handle_continue_ai)
        right_layout.addWidget(btn_next_stage)

        splitter.addWidget(right_widget)

        layout.addWidget(splitter)

    def set_active_project(self, project: Project):
        """Set active project and load existing sources/chapters."""
        self.active_project = project
        self.reload_workspace()

    def reload_workspace(self):
        if not self.active_project:
            return

        sources = self.source_repo.list_by_project(self.active_project.id)
        if not sources:
            self.lbl_stats.setText("No source loaded for this project.")
            self.tbl_chapters.setRowCount(0)
            self.txt_original.clear()
            self.txt_cleaned.clear()
            return

        self.active_source = sources[0]
        meta = self.active_source.metadata
        self.lbl_stats.setText(
            f"Source: {self.active_source.uri_or_path} | Bytes: {meta.get('byte_count', 0)} | "
            f"Words: {meta.get('word_count', 0)} | Chars: {meta.get('char_count', 0)}"
        )

        chapters = self.chapter_repo.list_by_project(self.active_project.id)
        self.chapters_list = chapters
        self.tbl_chapters.setRowCount(len(chapters))

        for idx, c in enumerate(chapters):
            self.tbl_chapters.setItem(idx, 0, QTableWidgetItem(str(c.sequence_index)))
            self.tbl_chapters.setItem(idx, 1, QTableWidgetItem(str(c.chapter_number)))
            self.tbl_chapters.setItem(idx, 2, QTableWidgetItem(c.title))

        if chapters:
            self.display_chapter(chapters[0])

    def handle_chapter_selected(self, row: int, col: int):
        if 0 <= row < len(self.chapters_list):
            self.display_chapter(self.chapters_list[row])

    def display_chapter(self, chapter: Chapter):
        self.active_chapter = chapter
        self.session_ctx.set_active_chapter(chapter.id)
        self.txt_edit_cnum.setText(str(chapter.chapter_number))
        self.txt_edit_title.setText(chapter.title)
        self.txt_original.setPlainText(chapter.original_text)
        self.txt_cleaned.setPlainText(chapter.cleaned_text)

    def handle_save_override(self):
        if not self.active_chapter:
            return

        try:
            new_cnum = int(self.txt_edit_cnum.text().strip())
        except ValueError:
            new_cnum = self.active_chapter.chapter_number

        new_title = self.txt_edit_title.text().strip()
        new_cleaned = self.txt_cleaned.toPlainText()

        self.content_engine.apply_manual_chapter_override(
            self.active_chapter.id,
            new_chapter_number=new_cnum,
            new_title=new_title,
            new_cleaned_text=new_cleaned,
        )
        self.reload_workspace()

    def handle_import_file(self):
        if not self.active_project:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Story TXT File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.content_engine.process_file_source(self.active_project.id, file_path)
            self.reload_workspace()

    def handle_continue_ai(self):
        if self.on_navigate_stage:
            self.on_navigate_stage(4)  # Index 4 is AI Director
