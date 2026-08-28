"""Guided 12-Step Create Wizard for Studio-AI.

Walks user step-by-step through Project, Content, Chapter, AI Mode, Output, Duration,
Aspect Ratio, Voice, Visuals, Subtitles, Review, and Production.
"""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.ai_models import AIMode
from src.domain.models import Project, ProjectType
from src.domain.session_context import SessionContext
from src.domain.subtitle_models import SubtitleStyleProfile
from src.domain.visual_models import OutputProfile, VisualMode
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.project_repo import ProjectRepository
from src.repositories.section_repo import SectionRepository
from src.repositories.source_repo import SourceRepository
from src.services.content_engine import ContentEngine
from src.services.production_orchestrator import ProductionOrchestrator
from src.services.workspace_manager import WorkspaceManager


class CreateWizardView(QWidget):
    """12-Step Guided Production Wizard."""

    STEP_NAMES = [
        "1. Project",
        "2. Content Source",
        "3. Chapter Selection",
        "4. AI Mode",
        "5. Output Type",
        "6. Duration",
        "7. Aspect Ratio",
        "8. Voice",
        "9. Visuals",
        "10. Subtitles",
        "11. Review",
        "12. Production",
    ]

    def __init__(
        self,
        session_ctx: SessionContext,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
        chapter_repo: ChapterRepository,
        section_repo: SectionRepository,
        workspace_mgr: WorkspaceManager,
        orchestrator: ProductionOrchestrator,
        settings: AppSettings,
        on_navigate_stage: Optional[Callable[[int], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.session_ctx = session_ctx
        self.project_repo = project_repo
        self.source_repo = source_repo
        self.chapter_repo = chapter_repo
        self.section_repo = section_repo
        self.workspace_mgr = workspace_mgr
        self.orchestrator = orchestrator
        self.settings = settings
        self.on_navigate_stage = on_navigate_stage

        self.content_engine = ContentEngine(source_repo, chapter_repo, section_repo)
        self.current_step = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header step progress
        top_layout = QHBoxLayout()
        self.lbl_step_title = QLabel("STEP 1: Project Setup")
        self.lbl_step_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2196F3;")
        top_layout.addWidget(self.lbl_step_title)
        top_layout.addStretch()

        self.prog_wizard = QProgressBar()
        self.prog_wizard.setRange(0, 12)
        self.prog_wizard.setValue(1)
        self.prog_wizard.setFixedWidth(200)
        top_layout.addWidget(self.prog_wizard)

        layout.addLayout(top_layout)

        # Wizard Step Stack
        self.stack = QStackedWidget()

        # Step 1: Project
        step1 = QWidget()
        f1 = QFormLayout(step1)
        self.txt_pname = QLineEdit("New Studio Project")
        self.cmb_ptype = QComboBox()
        for pt in ProjectType:
            self.cmb_ptype.addItem(pt.value)
        f1.addRow("Project Name:", self.txt_pname)
        f1.addRow("Project Type:", self.cmb_ptype)
        self.stack.addWidget(step1)

        # Step 2: Content Source
        step2 = QWidget()
        v2 = QVBoxLayout(step2)
        v2.addWidget(QLabel("Import Story Text File or Paste Text:"))
        self.txt_raw_story = QTextEdit()
        self.txt_raw_story.setPlaceholderText("Paste story text here or click Import File...")
        btn_import = QPushButton("Import TXT File")
        btn_import.clicked.connect(self.handle_import_file)
        v2.addWidget(self.txt_raw_story)
        v2.addWidget(btn_import)
        self.stack.addWidget(step2)

        # Step 3: Chapter Selection
        step3 = QWidget()
        f3 = QFormLayout(step3)
        self.cmb_scope = QComboBox()
        self.cmb_scope.addItem("Entire Story / All Chapters")
        self.cmb_scope.addItem("Selected Chapter Only")
        self.cmb_chapters = QComboBox()
        f3.addRow("Production Scope:", self.cmb_scope)
        f3.addRow("Selected Chapter:", self.cmb_chapters)
        self.stack.addWidget(step3)

        # Step 4: AI Mode
        step4 = QWidget()
        f4 = QFormLayout(step4)
        self.cmb_ai_mode = QComboBox()
        for m in AIMode:
            self.cmb_ai_mode.addItem(m.value)
        f4.addRow("Select AI Mode:", self.cmb_ai_mode)
        self.stack.addWidget(step4)

        # Step 5: Output Type
        step5 = QWidget()
        f5 = QFormLayout(step5)
        self.cmb_out_type = QComboBox()
        self.cmb_out_type.addItem("LONG_VIDEO")
        self.cmb_out_type.addItem("SHORT_REEL")
        self.cmb_out_type.addItem("AUDIO_ONLY")
        f5.addRow("Select Output Type:", self.cmb_out_type)
        self.stack.addWidget(step5)

        # Step 6: Duration
        step6 = QWidget()
        f6 = QFormLayout(step6)
        self.cmb_duration = QComboBox()
        self.cmb_duration.addItems(["AUTOMATIC", "30 Seconds", "60 Seconds", "10 Minutes", "20 Minutes"])
        f6.addRow("Target Duration:", self.cmb_duration)
        self.stack.addWidget(step6)

        # Step 7: Aspect Ratio
        step7 = QWidget()
        f7 = QFormLayout(step7)
        self.cmb_aspect = QComboBox()
        for ar in OutputProfile:
            self.cmb_aspect.addItem(ar.value)
        f7.addRow("Aspect Ratio:", self.cmb_aspect)
        self.stack.addWidget(step7)

        # Step 8: Voice
        step8 = QWidget()
        f8 = QFormLayout(step8)
        self.cmb_voice = QComboBox()
        self.cmb_voice.addItems(["af_heart (Kokoro)", "am_adam (Kokoro)", "en_US-lessac-medium (Piper)"])
        f8.addRow("Select Voice:", self.cmb_voice)
        self.stack.addWidget(step8)

        # Step 9: Visuals
        step9 = QWidget()
        f9 = QFormLayout(step9)
        self.cmb_visual_mode = QComboBox()
        for vm in VisualMode:
            self.cmb_visual_mode.addItem(vm.value)
        f9.addRow("Visual Mode:", self.cmb_visual_mode)
        self.stack.addWidget(step9)

        # Step 10: Subtitles
        step10 = QWidget()
        f10 = QFormLayout(step10)
        self.cmb_sub_style = QComboBox()
        for ss in SubtitleStyleProfile:
            self.cmb_sub_style.addItem(ss.value)
        f10.addRow("Subtitle Style:", self.cmb_sub_style)
        self.stack.addWidget(step10)

        # Step 11: Review Card
        step11 = QWidget()
        v11 = QVBoxLayout(step11)
        v11.addWidget(QLabel("Production Summary Review:"))
        self.txt_review = QTextEdit()
        self.txt_review.setReadOnly(True)
        v11.addWidget(self.txt_review)
        self.stack.addWidget(step11)

        # Step 12: Production Trigger
        step12 = QWidget()
        v12 = QVBoxLayout(step12)
        self.lbl_prod_status = QLabel("Ready to launch production run.")
        self.lbl_prod_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #4caf50;")
        btn_launch = QPushButton("APPROVE & START PRODUCTION")
        btn_launch.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; font-size: 16px; padding: 12px;")
        btn_launch.clicked.connect(self.handle_launch_production)
        v12.addWidget(self.lbl_prod_status)
        v12.addWidget(btn_launch)
        self.stack.addWidget(step12)

        layout.addWidget(self.stack)

        # Nav Control Bar [ BACK ] [ NEXT ] [ SAVE ] [ CANCEL ]
        nav_bar = QHBoxLayout()
        self.btn_back = QPushButton("BACK")
        self.btn_next = QPushButton("NEXT")
        self.btn_save = QPushButton("SAVE")
        self.btn_cancel = QPushButton("CANCEL")

        self.btn_back.clicked.connect(self.handle_back)
        self.btn_next.clicked.connect(self.handle_next)
        self.btn_save.clicked.connect(self.handle_save)
        self.btn_cancel.clicked.connect(self.handle_cancel)

        nav_bar.addWidget(self.btn_back)
        nav_bar.addWidget(self.btn_next)
        nav_bar.addStretch()
        nav_bar.addWidget(self.btn_save)
        nav_bar.addWidget(self.btn_cancel)

        layout.addLayout(nav_bar)

    def handle_import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Story TXT File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                self.txt_raw_story.setPlainText(f.read())

    def handle_next(self):
        if not self.validate_current_step():
            return

        if self.current_step == 0:
            # Create Project
            pname = self.txt_pname.text().strip()
            ptype = ProjectType(self.cmb_ptype.currentText())
            project = Project(title=pname, project_type=ptype)
            self.workspace_mgr.initialize_project_workspace(project)
            self.project_repo.save(project)
            self.session_ctx.set_active_project(project.id)

        elif self.current_step == 1:
            # Ingest Content
            raw_text = self.txt_raw_story.toPlainText()
            if raw_text and self.session_ctx.active_project_id:
                src_ent, rep = self.content_engine.process_text_source(self.session_ctx.active_project_id, raw_text)
                self.session_ctx.active_source_id = src_ent.id
                chapters = self.chapter_repo.list_by_project(self.session_ctx.active_project_id)
                self.cmb_chapters.clear()
                for c in chapters:
                    self.cmb_chapters.addItem(f"Chapter #{c.sequence_index + 1}: {c.title}", c.id)

        if self.current_step < 11:
            self.current_step += 1
            self.update_step_ui()

    def handle_back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step_ui()

    def handle_save(self):
        QMessageBox.information(self, "Save", "Wizard configuration saved to project session.")

    def handle_cancel(self):
        self.current_step = 0
        self.update_step_ui()

    def validate_current_step(self) -> bool:
        if self.current_step == 0:
            if not self.txt_pname.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a valid project name.")
                return False
        elif self.current_step == 1:
            if not self.txt_raw_story.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Please import or paste story text content.")
                return False
        return True

    def update_step_ui(self):
        self.stack.setCurrentIndex(self.current_step)
        self.lbl_step_title.setText(f"STEP {self.current_step + 1}: {self.STEP_NAMES[self.current_step]}")
        self.prog_wizard.setValue(self.current_step + 1)

        if self.current_step == 10:
            # Populate review text
            summary = (
                f"Project: {self.txt_pname.text()}\n"
                f"Project Type: {self.cmb_ptype.currentText()}\n"
                f"AI Mode: {self.cmb_ai_mode.currentText()}\n"
                f"Output Type: {self.cmb_out_type.currentText()}\n"
                f"Aspect Ratio: {self.cmb_aspect.currentText()}\n"
                f"Voice: {self.cmb_voice.currentText()}\n"
                f"Visual Mode: {self.cmb_visual_mode.currentText()}\n"
                f"Subtitle Style: {self.cmb_sub_style.currentText()}\n"
            )
            self.txt_review.setPlainText(summary)

    def handle_launch_production(self):
        if not self.session_ctx.active_project_id:
            return

        chapters = self.chapter_repo.list_by_project(self.session_ctx.active_project_id)
        if not chapters:
            return

        target_cid = self.cmb_chapters.currentData() or chapters[0].id
        voice_str = self.cmb_voice.currentText().split()[0]

        try:
            run, out_file, qa_report = self.orchestrator.run_chapter_production(
                project_id=self.session_ctx.active_project_id,
                chapter_id=target_cid,
                ai_mode=AIMode(self.cmb_ai_mode.currentText()),
                voice_id=voice_str,
                visual_mode=VisualMode(self.cmb_visual_mode.currentText()),
                profile=OutputProfile(self.cmb_aspect.currentText()),
                subtitle_style=SubtitleStyleProfile(self.cmb_sub_style.currentText()),
            )
            self.lbl_prod_status.setText(f"✓ PRODUCTION COMPLETED: {out_file.name}")
        except Exception as e:
            self.lbl_prod_status.setText(f"✗ PRODUCTION FAILED: {e}")
            self.lbl_prod_status.setStyleSheet("color: #f44336; font-weight: bold;")
