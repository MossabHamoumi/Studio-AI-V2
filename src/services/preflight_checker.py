"""Pre-Flight Checker for Production Orchestrator.

Validates all required dependencies (project, source, chapters, AI, TTS, FFmpeg, FFprobe,
disk space) before starting a production run. Fails loudly on missing dependencies.
"""

import shutil
from pathlib import Path
from typing import List, Tuple
from src.config.settings import AppSettings
from src.domain.ai_models import AIMode, AIStatus
from src.domain.models import Chapter, Project
from src.domain.tts_models import TTSProviderType
from src.repositories.chapter_repo import ChapterRepository
from src.repositories.source_repo import SourceRepository
from src.services.ai_provider import OllamaProvider
from src.services.tts_manager import FallbackTTSManager


class PreflightChecker:
    """Validates pre-flight conditions before initiating a ProductionRun."""

    def __init__(self, settings: AppSettings, chapter_repo: ChapterRepository, source_repo: SourceRepository):
        self.settings = settings
        self.chapter_repo = chapter_repo
        self.source_repo = source_repo
        self.ollama_provider = OllamaProvider()
        self.tts_manager = FallbackTTSManager(settings)

    def check_preflight(
        self,
        project: Project,
        chapter_ids: List[str],
        ai_mode: AIMode = AIMode.AI_FULL,
        voice_id: str = "af_heart",
    ) -> Tuple[bool, List[str]]:
        """Run all mandatory pre-flight checks and return (is_passed, errors)."""
        errors: List[str] = []

        # 1. Project Check
        if not project or not project.id:
            errors.append("Preflight Failed: No active project specified.")
            return False, errors

        # 2. Chapters Check
        if not chapter_ids:
            errors.append("Preflight Failed: No chapters selected for production run.")
            return False, errors

        for cid in chapter_ids:
            try:
                ch = self.chapter_repo.get_by_id(cid)
                if not ch.original_text and not ch.cleaned_text:
                    errors.append(f"Preflight Failed: Chapter '{cid}' has no text content.")
            except Exception:
                errors.append(f"Preflight Failed: Chapter '{cid}' not found in database.")

        # 3. Source Check
        sources = self.source_repo.list_by_project(project.id)
        if not sources:
            errors.append(f"Preflight Failed: Project '{project.title}' has no registered source documents.")

        # 4. Local AI Check (if required by mode)
        if ai_mode in (AIMode.AI_FULL, AIMode.AI_ASSISTED):
            health = self.ollama_provider.check_health()
            if health in (AIStatus.UNAVAILABLE, AIStatus.OFFLINE):
                errors.append(
                    f"Preflight Failed: Ollama AI server is {health.value} at {self.ollama_provider.base_url}."
                )

        # 5. Local TTS Engine Check
        voices = self.tts_manager.get_available_voices()
        available_voices = [v for v in voices if v.is_available]
        if not available_voices:
            errors.append("Preflight Failed: No neural TTS engines (Kokoro or Piper) are installed and available.")

        # 6. FFmpeg / FFprobe Binary Checks
        if not shutil.which("ffmpeg"):
            errors.append("Preflight Failed: FFmpeg CLI executable is not installed or not in system PATH.")

        if not shutil.which("ffprobe"):
            errors.append("Preflight Failed: FFprobe CLI executable is not installed or not in system PATH.")

        # 7. Disk Space Check (> 500 MB)
        try:
            total, used, free = shutil.disk_usage(str(self.settings.workspace_dir))
            free_mb = free / (1024 * 1024)
            if free_mb < 500.0:
                errors.append(f"Preflight Failed: Insufficient disk space ({free_mb:.1f} MB free, minimum 500 MB required).")
        except Exception as e:
            errors.append(f"Preflight Failed: Could not verify disk space: {e}")

        is_passed = len(errors) == 0
        return is_passed, errors
