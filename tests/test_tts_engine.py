"""Tests for Real Local TTS and Narration Engine (Phase 4)."""

import math
import struct
import wave
from pathlib import Path
import pytest
from src.config.settings import AppSettings
from src.domain.tts_models import TTSProviderType
from src.services.narration_engine import NarrationEngine
from src.services.tts_chunker import TTSChunker
from src.services.tts_manager import FallbackTTSManager
from src.utilities.audio_validator import AudioValidator
from src.utilities.exceptions import StudioAIError


def create_synthetic_sine_wave(file_path: Path, freq: float = 440.0, duration: float = 2.0, sample_rate: int = 24000):
    """Generate a pure sine wave WAV file for testing pure tone rejection."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(sample_rate * duration)
    amplitude = 16000

    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        raw_bytes = bytearray()
        for i in range(num_samples):
            val = int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
            raw_bytes.extend(struct.pack("<h", val))

        wf.writeframes(bytes(raw_bytes))


def create_mock_speech_wave(file_path: Path, duration: float = 2.0, sample_rate: int = 24000):
    """Generate a pseudo-speech WAV file with varying frequencies for audio validator tests."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(sample_rate * duration)

    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        raw_bytes = bytearray()
        for i in range(num_samples):
            # Complex pseudo-speech wave with modulated frequency and noise
            freq = 150.0 + 80.0 * math.sin(2 * math.pi * 3.0 * i / sample_rate)
            val = int(12000 * math.sin(2 * math.pi * freq * i / sample_rate) * (0.8 + 0.2 * math.sin(i)))
            raw_bytes.extend(struct.pack("<h", val))

        wf.writeframes(bytes(raw_bytes))


def test_pure_sine_tone_rejection(tmp_path: Path):
    """Verify AudioValidator explicitly rejects pure synthetic sine wave tones."""
    validator = AudioValidator()
    sine_file = tmp_path / "pure_sine_440hz.wav"
    create_synthetic_sine_wave(sine_file, freq=440.0, duration=2.0)

    res = validator.validate_audio_file(sine_file)
    assert not res.is_valid
    assert res.is_pure_tone
    assert "pure sine tone" in res.error_message.lower()


def test_mock_speech_audio_validation(tmp_path: Path):
    """Verify AudioValidator passes valid speech-like audio."""
    validator = AudioValidator()
    speech_file = tmp_path / "mock_speech.wav"
    create_mock_speech_wave(speech_file, duration=2.0)

    res = validator.validate_audio_file(speech_file)
    assert res.is_valid
    assert not res.is_pure_tone
    assert not res.is_silent
    assert res.duration_seconds >= 1.9


def test_tts_chunker_natural_boundaries():
    """Verify TTSChunker targets ~180 words without creating micro-chunks."""
    chunker = TTSChunker()
    # Create 400 word paragraph text
    words = ["word" + str(i) for i in range(400)]
    sentences = [" ".join(words[i : i + 20]) + "." for i in range(0, 400, 20)]
    text = " ".join(sentences)

    specs = chunker.chunk_text(text, target_word_count=180, min_word_count=60)
    assert len(specs) >= 2
    # Non-tail chunks should be at least min_word_count
    for s in specs[:-1]:
        assert s.word_count >= 60


def test_tts_chunker_cache_key():
    """Verify deterministic cache key generation."""
    chunker = TTSChunker()
    k1 = chunker.compute_cache_key("Hello world", "KOKORO", "v0.19", "af_heart")
    k2 = chunker.compute_cache_key("Hello world", "KOKORO", "v0.19", "af_heart")
    assert k1 == k2
    assert len(k1) == 64


def test_fallback_tts_manager_failure_without_engines(tmp_path: Path):
    """Verify FallbackTTSManager raises explicit error when real engines are unavailable."""
    settings = AppSettings(workspace_dir=tmp_path)
    manager = FallbackTTSManager(settings)

    # Disable mock availability to test failure
    manager.kokoro.is_available = lambda: False
    manager.piper.is_available = lambda: False

    out_dir = tmp_path / "audio_out"

    with pytest.raises(StudioAIError) as exc_info:
        manager.synthesize_text_chunk("Test speech synthesis", "af_heart", out_dir)

    assert "zero synthetic audio" in str(exc_info.value).lower()
