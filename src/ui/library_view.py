"""Library View for PySide6 Desktop UI.

Manages Voice Library, voice preview speech generation, and media asset tracking.
"""

from pathlib import Path
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
    QVBoxLayout,
    QWidget,
)
from src.config.settings import AppSettings
from src.domain.tts_models import TTSProviderType
from src.services.tts_manager import FallbackTTSManager
from src.utilities.audio_validator import AudioValidator


class LibraryView(QWidget):
    """Library View managing voice presets and real voice speech previews."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.tts_manager = FallbackTTSManager(settings)
        self.validator = AudioValidator()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Voice & Asset Library")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Voice Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Available Neural Voices:"))

        self.tbl_voices = QTableWidget()
        self.tbl_voices.setColumnCount(4)
        self.tbl_voices.setHorizontalHeaderLabels(["Provider", "Voice ID", "Display Name", "Available"])
        self.tbl_voices.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.tbl_voices)

        splitter.addWidget(left_widget)

        # Right: Real Voice Preview Generator
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        grp_preview = QGroupBox("Real Speech Voice Preview")
        form_preview = QFormLayout(grp_preview)

        self.txt_sample = QLineEdit("This is a real Studio AI narration test.")
        self.cmb_provider = QComboBox()
        self.cmb_provider.addItem("KOKORO")
        self.cmb_provider.addItem("PIPER")

        self.cmb_voice = QComboBox()
        self.cmb_voice.addItem("af_heart")
        self.cmb_voice.addItem("am_adam")
        self.cmb_voice.addItem("en_US-lessac-medium")

        btn_preview = QPushButton("Generate Real Speech Preview")
        btn_preview.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        btn_preview.clicked.connect(self.handle_generate_preview)

        self.lbl_preview_res = QLabel("Status: Ready")

        form_preview.addRow("Sample Text:", self.txt_sample)
        form_preview.addRow("Provider:", self.cmb_provider)
        form_preview.addRow("Voice ID:", self.cmb_voice)
        form_preview.addRow(btn_preview)
        form_preview.addRow(self.lbl_preview_res)

        right_layout.addWidget(grp_preview)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter)

        self.load_voices()

    def load_voices(self):
        voices = self.tts_manager.get_available_voices()
        self.tbl_voices.setRowCount(len(voices))

        for idx, v in enumerate(voices):
            self.tbl_voices.setItem(idx, 0, QTableWidgetItem(v.provider.value))
            self.tbl_voices.setItem(idx, 1, QTableWidgetItem(v.voice_id))
            self.tbl_voices.setItem(idx, 2, QTableWidgetItem(v.display_name))
            self.tbl_voices.setItem(idx, 3, QTableWidgetItem("Yes" if v.is_available else "No"))

    def handle_generate_preview(self):
        text = self.txt_sample.text().strip()
        voice_id = self.cmb_voice.currentText()
        provider_str = self.cmb_provider.currentText()
        provider = TTSProviderType.KOKORO if provider_str == "KOKORO" else TTSProviderType.PIPER

        preview_dir = self.settings.workspace_dir / "cache" / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)

        try:
            audio_path, duration, used_provider = self.tts_manager.synthesize_text_chunk(
                text=text,
                voice_id=voice_id,
                output_dir=preview_dir,
                preferred_provider=provider,
            )

            val_res = self.validator.validate_audio_file(audio_path)
            if val_res.is_valid:
                self.lbl_preview_res.setText(
                    f"✓ SUCCESS: Real speech preview generated ({duration:.2f}s) via {used_provider.value}"
                )
                self.lbl_preview_res.setStyleSheet("color: #4caf50; font-weight: bold;")
            else:
                self.lbl_preview_res.setText(f"✗ INVALID: {val_res.error_message}")
                self.lbl_preview_res.setStyleSheet("color: #f44336; font-weight: bold;")

        except Exception as e:
            self.lbl_preview_res.setText(f"✗ FAILED: {e}")
            self.lbl_preview_res.setStyleSheet("color: #f44336; font-weight: bold;")
