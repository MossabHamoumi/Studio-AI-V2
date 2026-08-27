"""Fallback TTS Manager and Audio Cache Engine.

Coordinates the Kokoro -> Piper -> FAILED fallback chain with audio cache reuse,
audio validation (rejects sine tones/silence), and structured logging to logs/tts.log.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple
from src.config.settings import AppSettings
from src.domain.tts_models import AudioChunk, TTSProviderType, TTSVoice
from src.providers.tts_kokoro import KokoroTTSProvider
from src.providers.tts_piper import PiperTTSProvider
from src.services.tts_chunker import TTSChunker
from src.utilities.audio_validator import AudioValidator
from src.utilities.exceptions import StudioAIError

logger = logging.getLogger("studio_ai.tts")


def setup_tts_logger(logs_dir: Path) -> logging.Logger:
    """Configure logs/tts.log logger."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    t_logger = logging.getLogger("studio_ai.tts")
    t_logger.setLevel(logging.INFO)
    if not t_logger.handlers:
        fh = logging.FileHandler(logs_dir / "tts.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s"))
        t_logger.addHandler(fh)
    return t_logger


class FallbackTTSManager:
    """Fallback TTS Manager running Kokoro -> Piper -> FAILED."""

    DEFAULT_PIPER_VOICE = "en_US-lessac-medium"

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.kokoro = KokoroTTSProvider()
        self.piper = PiperTTSProvider()
        self.chunker = TTSChunker()
        self.validator = AudioValidator()
        self.tts_logger = setup_tts_logger(settings.logs_dir)

    def get_available_voices(self) -> List[TTSVoice]:
        """List all available voices across Kokoro and Piper."""
        voices: List[TTSVoice] = []
        voices.extend(self.kokoro.list_voices())
        voices.extend(self.piper.list_voices())
        return voices

    def synthesize_text_chunk(
        self,
        text: str,
        voice_id: str,
        output_dir: Path,
        preferred_provider: TTSProviderType = TTSProviderType.KOKORO,
    ) -> Tuple[Path, float, TTSProviderType]:
        """Synthesize chunk using Kokoro -> Piper fallback chain with audio validation."""
        output_dir.mkdir(parents=True, exist_ok=True)

        cache_key = self.chunker.compute_cache_key(
            text=text,
            provider=preferred_provider.value,
            model="default",
            voice=voice_id,
        )
        cached_file = output_dir / f"chunk_{cache_key[:12]}.wav"

        # Check Cache Hit
        if cached_file.exists():
            val_res = self.validator.validate_audio_file(cached_file)
            if val_res.is_valid:
                self.tts_logger.info(f"CACHE HIT: Reusing chunk {cached_file.name}")
                return cached_file, val_res.duration_seconds, preferred_provider

        # Attempt 1: Kokoro Primary
        if self.kokoro.is_available():
            try:
                self.tts_logger.info(f"Attempting primary synthesis with Kokoro ({voice_id})...")
                duration = self.kokoro.synthesize_speech(text, voice_id, cached_file)
                val_res = self.validator.validate_audio_file(cached_file)
                if val_res.is_valid:
                    self.tts_logger.info("Kokoro SUCCESS")
                    return cached_file, duration, TTSProviderType.KOKORO
                else:
                    self.tts_logger.warning(f"Kokoro output validation failed: {val_res.error_message}")
            except Exception as e:
                self.tts_logger.warning(f"Kokoro FAILED: {e}")

        # Attempt 2: Piper Fallback
        if self.piper.is_available():
            piper_voice = voice_id if voice_id.startswith("en_US") else self.DEFAULT_PIPER_VOICE
            try:
                self.tts_logger.info(f"Fallback attempt with Piper ({piper_voice})...")
                duration = self.piper.synthesize_speech(text, piper_voice, cached_file)
                val_res = self.validator.validate_audio_file(cached_file)
                if val_res.is_valid:
                    self.tts_logger.info("Piper SUCCESS (Fallback from Kokoro)")
                    return cached_file, duration, TTSProviderType.PIPER
                else:
                    self.tts_logger.warning(f"Piper output validation failed: {val_res.error_message}")
            except Exception as e:
                self.tts_logger.warning(f"Piper FAILED: {e}")

        # Final State: FAILED
        self.tts_logger.error("TTS Synthesis FAILED: Neither Kokoro nor Piper TTS engines are available or succeeded.")
        raise StudioAIError(
            "TTS Engine Failure: Real TTS engines (Kokoro/Piper) are unavailable or failed audio validation. Zero synthetic audio generated per ground rules."
        )
