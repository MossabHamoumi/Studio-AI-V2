"""Visual Studio View for PySide6 Desktop UI.

Manages visual mode selection, output profiles, image/gameplay clip selection,
editable AI image prompts, title card options, and visual layout preview.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.models import Chapter, Project
from src.domain.visual_models import (
    MotionEffect,
    OutputProfile,
    ScalingMode,
    VisualMode,
)
from src.repositories.asset_repo import AssetRepository
from src.repositories.chapter_repo import ChapterRepository
from src.services.asset_library import AssetLibraryService
from src.services.visual_planner import VisualPlanner


class VisualView(QWidget):
    """Visual Studio UI View."""

    def __init__(
        self,
        asset_repo: AssetRepository,
        chapter_repo: ChapterRepository,
        settings: AppSettings,
        parent=None,
    ):
        super().__init__(parent)
        self.asset_repo = asset_repo
        self.chapter_repo = chapter_repo
        self.settings = settings
        self.asset_service = AssetLibraryService(asset_repo)
        self.planner = VisualPlanner(settings)

        self.active_project: Optional[Project] = None
        self.active_chapter: Optional[Chapter] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Visual Studio & Layout Planner")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Mode & Profile Controls
        header_group = QGroupBox("Visual Mode & Format Profile")
        header_form = QFormLayout(header_group)

        self.cmb_mode = QComboBox()
        for mode in VisualMode:
            self.cmb_mode.addItem(mode.value)

        self.cmb_profile = QComboBox()
        for prof in OutputProfile:
            self.cmb_profile.addItem(prof.value)

        self.cmb_scaling = QComboBox()
        for sc in ScalingMode:
            self.cmb_scaling.addItem(sc.value)

        self.cmb_motion = QComboBox()
        for m in MotionEffect:
            self.cmb_motion.addItem(m.value)

        header_form.addRow("Visual Mode:", self.cmb_mode)
        header_form.addRow("Output Profile:", self.cmb_profile)
        header_form.addRow("Image Scaling:", self.cmb_scaling)
        header_form.addRow("Motion Effect:", self.cmb_motion)

        layout.addWidget(header_group)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: AI Image Prompt & Title Card Form
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        grp_prompt = QGroupBox("Editable AI Image Prompt")
        vbox_prompt = QVBoxLayout(grp_prompt)
        self.txt_prompt = QTextEdit()
        btn_gen_prompt = QPushButton("Generate AI Image Prompt")
        btn_gen_prompt.clicked.connect(self.handle_generate_prompt)

        vbox_prompt.addWidget(self.txt_prompt)
        vbox_prompt.addWidget(btn_gen_prompt)
        left_layout.addWidget(grp_prompt)

        grp_title = QGroupBox("Title Card Overlay")
        form_title = QFormLayout(grp_title)
        self.txt_title = QLineEdit("Story Title")
        self.txt_subtitle = QLineEdit("A Local AI Production")
        form_title.addRow("Title:", self.txt_title)
        form_title.addRow("Subtitle:", self.txt_subtitle)
        left_layout.addWidget(grp_title)

        splitter.addWidget(left_widget)

        # Right Panel: Layout Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        grp_preview = QGroupBox("Visual Layout Preview")
        vbox_preview = QVBoxLayout(grp_preview)

        self.preview_frame = QFrame()
        self.preview_frame.setFrameShape(QFrame.StyledPanel)
        self.preview_frame.setStyleSheet("background-color: #111111; border: 2px solid #444;")
        self.preview_frame.setMinimumHeight(220)

        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setAlignment(Qt.AlignCenter)
        self.lbl_preview_title = QLabel("Title Card Overlay Preview")
        self.lbl_preview_title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.lbl_preview_sub = QLabel("Subtitle Preview")
        self.lbl_preview_sub.setStyleSheet("color: #aaa; font-size: 14px;")

        preview_layout.addWidget(self.lbl_preview_title)
        preview_layout.addWidget(self.lbl_preview_sub)

        btn_save_plan = QPushButton("Save Visual Plan")
        btn_save_plan.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        btn_save_plan.clicked.connect(self.handle_save_plan)

        vbox_preview.addWidget(self.preview_frame)
        vbox_preview.addWidget(btn_save_plan)

        right_layout.addWidget(grp_preview)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter)

    def set_active_project(self, project: Project):
        self.active_project = project

    def handle_generate_prompt(self):
        prompt = self.planner.generate_editable_image_prompt(
            summary="Hero exploring ancient mysterious ruins",
            characters=["Hero"],
            tone="Dramatic",
            mood="Mysterious",
            aspect_ratio=self.cmb_profile.currentText(),
        )
        self.txt_prompt.setPlainText(prompt)

    def handle_save_plan(self):
        if not self.active_project:
            return

        plan = self.planner.create_visual_plan(
            project_id=self.active_project.id,
            chapter_id="current_chapter",
            mode=VisualMode(self.cmb_mode.currentText()),
            profile=OutputProfile(self.cmb_profile.currentText()),
            scaling=ScalingMode(self.cmb_scaling.currentText()),
            motion=MotionEffect(self.cmb_motion.currentText()),
            title=self.txt_title.text(),
            subtitle=self.txt_subtitle.text(),
            image_prompt=self.txt_prompt.toPlainText(),
        )

        self.lbl_preview_title.setText(plan.title_card.title)
        self.lbl_preview_sub.setText(plan.title_card.subtitle)
