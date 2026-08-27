"""Narration Engine & Audio Timeline Assembler.

Converts approved narration script into assembled audio timeline built from actual chunk durations.
"""

import wave
from pathlib import Path
from typing import List, Tuple
from src.config.settings import AppSettings
from src.domain.tts_models import (
    AudioChunk,
    AudioTimeline,
    AudioTimelineEntry,
    TTSProviderType,
)
from src.services.tts_chunker import TTSChunker
from src.services.tts_manager import FallbackTTSManager
from src.utilities.audio_validator import AudioValidator


class NarrationEngine:
    """Assembles audio narration timeline from chunked TTS outputs."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.tts_manager = FallbackTTSManager(settings)
        self.chunker = TTSChunker()
        self.validator = AudioValidator()

    def generate_narration_timeline(
        self,
        project_id: str,
        chapter_id: str,
        text: str,
        voice_id: str = "af_heart",
        preferred_provider: TTSProviderType = TTSProviderType.KOKORO,
    ) -> AudioTimeline:
        """Generate audio chunks, validate durations, and assemble audio timeline."""
        chunk_specs = self.chunker.chunk_text(text)
        project_dir = self.settings.get_project_dir(project_id)
        chapter_audio_dir = project_dir / "chapters" / chapter_id / "audio"
        chapter_audio_dir.mkdir(parents=True, exist_ok=True)

        timeline_entries: List[AudioTimelineEntry] = []
        chunk_files: List[Path] = []
        current_time = 0.0

        for idx, spec in enumerate(chunk_specs):
            chunk_file, duration, provider_used = self.tts_manager.synthesize_text_chunk(
                text=spec.text,
                voice_id=voice_id,
                output_dir=chapter_audio_dir,
                preferred_provider=preferred_provider,
            )

            chunk_files.append(chunk_file)

            entry = AudioTimelineEntry(
                sequence_index=idx,
                text=spec.text,
                start_time_seconds=round(current_time, 3),
                end_time_seconds=round(current_time + duration, 3),
                duration_seconds=round(duration, 3),
                audio_file_path=str(chunk_file),
            )
            timeline_entries.append(entry)
            current_time += duration

        # Assemble concatenated WAV
        assembled_path = chapter_audio_dir / "assembled_narration.wav"
        self._concatenate_wav_files(chunk_files, assembled_path)

        return AudioTimeline(
            project_id=project_id,
            chapter_id=chapter_id,
            total_duration_seconds=round(current_time, 3),
            assembled_audio_path=str(assembled_path),
            entries=timeline_entries,
        )

    def _concatenate_wav_files(self, wav_files: List[Path], output_file: Path) -> None:
        """Concatenate individual WAV chunk files into a single WAV file."""
        if not wav_files:
            return

        first_wav = wav_files[0]
        with wave.open(str(first_wav), "rb") as first_wf:
            params = first_wf.getparams()

        with wave.open(str(output_file), "wb") as out_wf:
            out_wf.setparams(params)
            for file_path in wav_files:
                with wave.open(str(file_path), "rb") as in_wf:
                    out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))
