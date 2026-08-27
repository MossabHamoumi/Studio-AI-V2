"""AI Director & Adaptation Service."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
from src.config.settings import AppSettings
from src.domain.ai_models import (
    AIMode,
    AIStatus,
    Adaptation,
    AdaptationStatus,
    Analysis,
    AnalysisType,
    normalize_enum_value,
)
from src.repositories.adaptation_repo import AdaptationRepository
from src.repositories.analysis_repo import AnalysisRepository
from src.services.ai_provider import LocalFallbackAnalyzer, OllamaProvider
from src.utilities.exceptions import StudioAIError, ValidationError


def setup_ai_loggers(logs_dir: Path) -> Tuple[logging.Logger, logging.Logger]:
    """Configure analysis.log and adaptation.log loggers."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s")

    # Analysis Logger
    analysis_logger = logging.getLogger("studio_ai.analysis")
    analysis_logger.setLevel(logging.INFO)
    if not analysis_logger.handlers:
        fh1 = logging.FileHandler(logs_dir / "analysis.log", encoding="utf-8")
        fh1.setFormatter(formatter)
        analysis_logger.addHandler(fh1)

    # Adaptation Logger
    adaptation_logger = logging.getLogger("studio_ai.adaptation")
    adaptation_logger.setLevel(logging.INFO)
    if not adaptation_logger.handlers:
        fh2 = logging.FileHandler(logs_dir / "adaptation.log", encoding="utf-8")
        fh2.setFormatter(formatter)
        adaptation_logger.addHandler(fh2)

    return analysis_logger, adaptation_logger


class AIDirector:
    """AI Director coordinating story analysis and listener script adaptation."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        adaptation_repo: AdaptationRepository,
        settings: AppSettings,
        ollama_provider: Optional[OllamaProvider] = None,
    ):
        self.analysis_repo = analysis_repo
        self.adaptation_repo = adaptation_repo
        self.settings = settings
        self.provider = ollama_provider or OllamaProvider()
        self.local_analyzer = LocalFallbackAnalyzer()

        self.analysis_logger, self.adaptation_logger = setup_ai_loggers(settings.logs_dir)

    def analyze_chapter(
        self,
        project_id: str,
        chapter_id: str,
        chapter_text: str,
        source_text_hash: str,
        mode: Union[AIMode, str] = AIMode.AI_FULL,
    ) -> Tuple[Analysis, AIStatus]:
        """Analyze chapter text using Ollama or local fallback based on AIMode and AIStatus."""
        ai_mode = normalize_enum_value(mode, AIMode)

        self.analysis_logger.info(
            f"Starting story analysis for project={project_id}, chapter={chapter_id}, mode={ai_mode.value}"
        )

        if ai_mode == AIMode.LOCAL_ONLY:
            analysis = self.local_analyzer.analyze_story_locally(
                project_id, chapter_id, chapter_text, source_text_hash
            )
            self.analysis_repo.save(analysis)
            self.analysis_logger.info(f"Completed LOCAL_ONLY analysis for chapter={chapter_id}")
            return analysis, AIStatus.OFFLINE

        # Probe Ollama health
        health = self.provider.check_health()
        if health != AIStatus.AVAILABLE:
            self.analysis_logger.warning(
                f"Ollama health check returned {health.value} for chapter={chapter_id}. Falling back to local analysis."
            )
            analysis = self.local_analyzer.analyze_story_locally(
                project_id, chapter_id, chapter_text, source_text_hash
            )
            self.analysis_repo.save(analysis)
            return analysis, health

        # Issue structured JSON prompt to Ollama
        system_prompt = (
            "You are an expert AI Story Director. Analyze the provided story text and return a JSON object with keys: "
            "summary, characters (array of strings), tone, mood, themes (array), estimated_duration_seconds (number)."
        )
        prompt = f"Story Chapter Text:\n{chapter_text}"

        try:
            res_json = self.provider.generate_json_response(prompt, system_prompt)
            words = chapter_text.split()
            duration = (len(words) / 150.0) * 60.0

            analysis = Analysis(
                project_id=project_id,
                chapter_id=chapter_id,
                summary=res_json.get("summary", "AI Generated Summary"),
                characters=res_json.get("characters", []),
                tone=res_json.get("tone", "Dramatic"),
                mood=res_json.get("mood", "Engaging"),
                themes=res_json.get("themes", []),
                estimated_duration_seconds=round(duration, 2),
                analysis_type=AnalysisType.AI_RESULT,
                model_used=self.provider.model,
                source_text_hash=source_text_hash,
            )
            self.analysis_repo.save(analysis)
            self.analysis_logger.info(f"Successfully saved AI_RESULT analysis for chapter={chapter_id}")
            return analysis, AIStatus.AVAILABLE
        except Exception as e:
            err_str = str(e).lower()
            status = AIStatus.TIMEOUT if "timed out" in err_str else AIStatus.UNAVAILABLE
            self.analysis_logger.error(f"Error during Ollama analysis ({status.value}) for chapter={chapter_id}: {e}")
            analysis = self.local_analyzer.analyze_story_locally(
                project_id, chapter_id, chapter_text, source_text_hash
            )
            self.analysis_repo.save(analysis)
            return analysis, status

    def adapt_chapter_script(
        self,
        project_id: str,
        chapter_id: str,
        chapter_text: str,
        source_text_hash: str,
        mode: Union[AIMode, str] = AIMode.AI_FULL,
    ) -> Tuple[Adaptation, AIStatus]:
        """Adapt story script for narration with strict validation checks."""
        ai_mode = normalize_enum_value(mode, AIMode)

        self.adaptation_logger.info(
            f"Starting script adaptation for project={project_id}, chapter={chapter_id}, mode={ai_mode.value}"
        )

        if ai_mode == AIMode.LOCAL_ONLY or self.provider.check_health() != AIStatus.AVAILABLE:
            # Deterministic local adaptation (clean line spacing)
            adapted_text = f"[Adapted for Narration]\n\n{chapter_text.strip()}"
            self.validate_adaptation_output(chapter_text, adapted_text)

            adaptation = Adaptation(
                project_id=project_id,
                chapter_id=chapter_id,
                adapted_text=adapted_text,
                source_text_hash=source_text_hash,
                model_used="LOCAL_FALLBACK",
                status=AdaptationStatus.PROPOSED,
            )
            self.adaptation_repo.save(adaptation)
            self.adaptation_logger.info(f"Saved local proposed adaptation for chapter={chapter_id}")
            return adaptation, AIStatus.OFFLINE

        # Issue adaptation prompt to Ollama
        system_prompt = "Adapt the story text into a clean narration script. Return JSON with key 'adapted_text'."
        prompt = f"Story Text:\n{chapter_text}"

        try:
            res_json = self.provider.generate_json_response(prompt, system_prompt)
            adapted_text = res_json.get("adapted_text", "").strip()

            self.validate_adaptation_output(chapter_text, adapted_text)

            adaptation = Adaptation(
                project_id=project_id,
                chapter_id=chapter_id,
                adapted_text=adapted_text,
                source_text_hash=source_text_hash,
                model_used=self.provider.model,
                status=AdaptationStatus.PROPOSED,
            )
            self.adaptation_repo.save(adaptation)
            self.adaptation_logger.info(f"Saved AI proposed adaptation for chapter={chapter_id}")
            return adaptation, AIStatus.AVAILABLE
        except Exception as e:
            self.adaptation_logger.error(f"Adaptation failed for chapter={chapter_id}: {e}")
            raise

    def validate_adaptation_output(self, original_text: str, adapted_text: str) -> None:
        """Reject empty, identical, or incomplete adaptations."""
        if not adapted_text or not adapted_text.strip():
            raise ValidationError("Adaptation failed: output is empty.")

        if adapted_text.strip() == original_text.strip():
            raise ValidationError("Adaptation rejected: output is identical to original text.")

        if len(adapted_text) < len(original_text) * 0.3:
            raise ValidationError("Adaptation rejected: output is severely incomplete (< 30% length).")

    def update_adaptation_status(
        self, adaptation_id: str, new_status: Union[AdaptationStatus, str]
    ) -> Adaptation:
        """Update review status (ACCEPT / REJECT / REGENERATE)."""
        status_enum = normalize_enum_value(new_status, AdaptationStatus)
        conn = self.adaptation_repo.db.get_connection()
        cursor = conn.execute("SELECT chapter_id FROM adaptations WHERE id = ?;", (adaptation_id,))
        row = cursor.fetchone()
        if not row:
            raise StudioAIError(f"Adaptation {adaptation_id} not found.")

        chapter_id = row["chapter_id"]
        adaptation = self.adaptation_repo.get_by_chapter(chapter_id)
        if not adaptation:
            raise StudioAIError(f"Adaptation for chapter {chapter_id} not found.")

        adaptation.status = status_enum
        return self.adaptation_repo.save(adaptation)
