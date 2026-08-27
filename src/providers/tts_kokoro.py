"""Kokoro-ONNX Neural TTS Provider."""

import wave
from pathlib import Path
from typing import List, Optional
from src.domain.tts_models import TTSProviderType, TTSVoice
from src.utilities.exceptions import StudioAIError


class KokoroTTSProvider:
    """Kokoro-ONNX TTS Engine Integration."""

    def __init__(self, model_dir: Optional[Path] = None):
        if model_dir is None:
            user_home = Path.home()
            self.model_dir = user_home / ".studio-ai" / "models" / "kokoro"
        else:
            self.model_dir = Path(model_dir)

        self.model_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices.json"
        self.provider_type = TTSProviderType.KOKORO

    def is_available(self) -> bool:
        """Probe Kokoro package import AND model file existence on disk."""
        try:
            import kokoro_onnx  # noqa: F401
            import soundfile    # noqa: F401
        except ImportError:
            return False

        # Verify model files exist
        return self.model_path.is_file() and self.voices_path.is_file()

    def list_voices(self) -> List[TTSVoice]:
        """List supported Kokoro neural voices."""
        avail = self.is_available()
        return [
            TTSVoice(
                provider=self.provider_type,
                voice_id="af_heart",
                display_name="Kokoro - Heart (Female)",
                language="en-us",
                is_available=avail,
                sample_rate=24000,
            ),
            TTSVoice(
                provider=self.provider_type,
                voice_id="am_adam",
                display_name="Kokoro - Adam (Male)",
                language="en-us",
                is_available=avail,
                sample_rate=24000,
            ),
        ]

    def synthesize_speech(
        self, text: str, voice_id: str, output_path: Path, rate: float = 1.0
    ) -> float:
        """Synthesize text to speech WAV file using Kokoro-ONNX or fail clearly."""
        if not self.is_available():
            raise StudioAIError(
                f"Kokoro TTS engine is unavailable (`kokoro-onnx` library or model files at '{self.model_dir}' missing)."
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from kokoro_onnx import Kokoro
            import soundfile as sf

            kokoro = Kokoro(str(self.model_path), str(self.voices_path))
            samples, sample_rate = kokoro.create(text, voice=voice_id, speed=rate, lang="en-us")

            sf.write(str(output_path), samples, sample_rate)

            duration = len(samples) / float(sample_rate)
            return round(duration, 3)
        except Exception as e:
            raise StudioAIError(f"Kokoro synthesis failed for voice '{voice_id}': {e}") from e
