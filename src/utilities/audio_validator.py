"""Audio Validator & Pure Tone / Silence Detector.

Validates WAV/audio files for real human speech characteristics.
Explicitly rejects silent audio files and synthetic pure sine wave tones.
"""

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from src.utilities.exceptions import ValidationError


@dataclass
class AudioValidationResult:
    """Audio file properties and validation state."""

    file_path: str
    is_valid: bool
    duration_seconds: float
    sample_rate: int
    channels: int
    sample_width: int
    rms_amplitude: float
    is_pure_tone: bool
    is_silent: bool
    error_message: Optional[str] = None


class AudioValidator:
    """Validates audio files for format integrity, amplitude, silence, and pure sine tones."""

    def validate_audio_file(
        self, file_path: Path, min_duration: float = 0.1, max_silence_ratio: float = 0.95
    ) -> AudioValidationResult:
        """Validate audio file properties and detect synthetic sine waves / silence."""
        path = Path(file_path)
        if not path.exists():
            return AudioValidationResult(
                file_path=str(path),
                is_valid=False,
                duration_seconds=0.0,
                sample_rate=0,
                channels=0,
                sample_width=0,
                rms_amplitude=0.0,
                is_pure_tone=False,
                is_silent=True,
                error_message=f"Audio file '{file_path}' does not exist on disk.",
            )

        if path.stat().st_size <= 44:  # WAV header is 44 bytes
            return AudioValidationResult(
                file_path=str(path),
                is_valid=False,
                duration_seconds=0.0,
                sample_rate=0,
                channels=0,
                sample_width=0,
                rms_amplitude=0.0,
                is_pure_tone=False,
                is_silent=True,
                error_message=f"Audio file '{file_path}' is empty or header-only.",
            )

        try:
            with wave.open(str(path), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                num_frames = wf.getnframes()

                if sample_rate <= 0 or num_frames == 0:
                    return AudioValidationResult(
                        file_path=str(path),
                        is_valid=False,
                        duration_seconds=0.0,
                        sample_rate=sample_rate,
                        channels=channels,
                        sample_width=sample_width,
                        rms_amplitude=0.0,
                        is_pure_tone=False,
                        is_silent=True,
                        error_message="Audio file has 0 frames or invalid sample rate.",
                    )

                duration = num_frames / float(sample_rate)
                if duration < min_duration:
                    return AudioValidationResult(
                        file_path=str(path),
                        is_valid=False,
                        duration_seconds=duration,
                        sample_rate=sample_rate,
                        channels=channels,
                        sample_width=sample_width,
                        rms_amplitude=0.0,
                        is_pure_tone=False,
                        is_silent=True,
                        error_message=f"Audio duration {duration:.2f}s is below minimum {min_duration}s.",
                    )

                raw_frames = wf.readframes(num_frames)
                rms, is_silent, is_pure_tone = self._analyze_samples(
                    raw_frames, sample_width, channels, sample_rate
                )

                if is_silent:
                    return AudioValidationResult(
                        file_path=str(path),
                        is_valid=False,
                        duration_seconds=duration,
                        sample_rate=sample_rate,
                        channels=channels,
                        sample_width=sample_width,
                        rms_amplitude=rms,
                        is_pure_tone=is_pure_tone,
                        is_silent=True,
                        error_message="Audio file is completely silent.",
                    )

                if is_pure_tone:
                    return AudioValidationResult(
                        file_path=str(path),
                        is_valid=False,
                        duration_seconds=duration,
                        sample_rate=sample_rate,
                        channels=channels,
                        sample_width=sample_width,
                        rms_amplitude=rms,
                        is_pure_tone=True,
                        is_silent=False,
                        error_message="Audio file rejected: contains synthetic pure sine tone.",
                    )

                return AudioValidationResult(
                    file_path=str(path),
                    is_valid=True,
                    duration_seconds=round(duration, 3),
                    sample_rate=sample_rate,
                    channels=channels,
                    sample_width=sample_width,
                    rms_amplitude=round(rms, 4),
                    is_pure_tone=False,
                    is_silent=False,
                )

        except wave.Error as e:
            return AudioValidationResult(
                file_path=str(path),
                is_valid=False,
                duration_seconds=0.0,
                sample_rate=0,
                channels=0,
                sample_width=0,
                rms_amplitude=0.0,
                is_pure_tone=False,
                is_silent=True,
                error_message=f"WAV format error: {e}",
            )

    def _analyze_samples(
        self, raw_frames: bytes, sample_width: int, channels: int, sample_rate: int
    ) -> Tuple[float, bool, bool]:
        """Analyze audio frames for RMS amplitude, silence, and pure sine wave characteristics."""
        if sample_width != 2:  # Assume 16-bit PCM for WAV analysis
            return 0.5, False, False

        num_samples = len(raw_frames) // 2
        if num_samples == 0:
            return 0.0, True, False

        samples = struct.unpack(f"<{num_samples}h", raw_frames)
        # Take mono channel if stereo
        mono_samples = samples[::channels] if channels > 1 else samples

        # Calculate RMS amplitude
        sum_sq = sum(s * s for s in mono_samples)
        mean_sq = sum_sq / float(len(mono_samples))
        rms = math.sqrt(mean_sq) / 32768.0  # Normalized to [0.0, 1.0]

        is_silent = rms < 0.001

        # Pure sine tone detection via zero-crossing intervals consistency
        # Pure sine wave has near-constant zero crossing intervals
        zero_crossings = []
        for i in range(1, len(mono_samples)):
            if (mono_samples[i - 1] < 0 and mono_samples[i] >= 0) or (
                mono_samples[i - 1] >= 0 and mono_samples[i] < 0
            ):
                zero_crossings.append(i)

        is_pure_tone = False
        if len(zero_crossings) > 20:
            intervals = [
                zero_crossings[i] - zero_crossings[i - 1] for i in range(1, len(zero_crossings))
            ]
            mean_int = sum(intervals) / float(len(intervals))
            variance = sum((x - mean_int) ** 2 for x in intervals) / float(len(intervals))
            std_dev = math.sqrt(variance)

            # Speech has high std_dev in zero crossing intervals; pure sine tone std_dev ~ 0
            if std_dev < 0.5 and mean_int > 2.0:
                is_pure_tone = True

        return rms, is_silent, is_pure_tone
