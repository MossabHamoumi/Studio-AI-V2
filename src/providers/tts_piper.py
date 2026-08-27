"""Piper ONNX/Executable Local TTS Provider."""

import wave
from pathlib import Path
from typing import List, Optional
from src.domain.tts_models import TTSProviderType, TTSVoice
from src.utilities.exceptions import StudioAIError


class PiperTTSProvider:
    """Piper TTS Engine Integration."""

    def __init__(self, model_dir: Optional[Path] = None):
        if model_dir is None:
            user_home = Path.home()
            self.model_dir = user_home / ".studio-ai" / "models" / "piper"
        else:
            self.model_dir = Path(model_dir)

        self.provider_type = TTSProviderType.PIPER

    def is_available(self) -> bool:
        """Probe Piper package import AND model file presence."""
        try:
            import piper  # noqa: F401
        except ImportError:
            return False

        if not self.model_dir.exists():
            return False

        onnx_models = list(self.model_dir.glob("*.onnx"))
        return len(onnx_models) > 0

    def list_voices(self) -> List[TTSVoice]:
        """List supported Piper voices."""
        avail = self.is_available()
        return [
            TTSVoice(
                provider=self.provider_type,
                voice_id="en_US-lessac-medium",
                display_name="Piper - Lessac (Female)",
                language="en-us",
                is_available=avail,
                sample_rate=22050,
            ),
            TTSVoice(
                provider=self.provider_type,
                voice_id="en_US-ryan-medium",
                display_name="Piper - Ryan (Male)",
                language="en-us",
                is_available=avail,
                sample_rate=22050,
            ),
        ]

    def synthesize_speech(
        self, text: str, voice_id: str, output_path: Path, rate: float = 1.0
    ) -> float:
        """Synthesize text to speech WAV file using Piper or fail clearly."""
        if not self.is_available():
            raise StudioAIError(
                f"Piper TTS engine is unavailable (`piper-tts` library or model files at '{self.model_dir}' missing)."
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        model_file = self.model_dir / f"{voice_id}.onnx"

        if not model_file.is_file():
            raise StudioAIError(f"Piper model file '{model_file}' not found.")

        try:
            from piper import PiperVoice
            voice = PiperVoice.load(str(model_file))
            with wave.open(str(output_path), "wb") as wav_file:
                voice.synthesize(text, wav_file)

            with wave.open(str(output_path), "rb") as wf:
                duration = wf.getnframes() / float(wf.getframerate())
                return round(duration, 3)
        except Exception as e:
            raise StudioAIError(f"Piper synthesis failed for voice '{voice_id}': {e}") from e
