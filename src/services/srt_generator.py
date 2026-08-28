"""Standard SubRip Subtitle (SRT) Generator."""

from pathlib import Path
from typing import List
from src.domain.subtitle_models import SubtitleEvent


class SRTGenerator:
    """Generates standard SRT formatted subtitle files."""

    def generate_srt(self, events: List[SubtitleEvent], output_path: Path) -> Path:
        """Generate SRT subtitle file on disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        srt_blocks = []
        for idx, ev in enumerate(events, 1):
            start_str = self._format_srt_timestamp(ev.start_time_seconds)
            end_str = self._format_srt_timestamp(ev.end_time_seconds)
            block = f"{idx}\n{start_str} --> {end_str}\n{ev.text.strip()}\n"
            srt_blocks.append(block)

        full_content = "\n".join(srt_blocks) + "\n"
        output_path.write_text(full_content, encoding="utf-8")
        return output_path

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format `HH:MM:SS,mmm` (milliseconds)."""
        secs = max(0.0, seconds)
        hours = int(secs // 3600)
        minutes = int((secs % 3600) // 60)
        rem_secs = secs % 60
        sec_int = int(rem_secs)
        millis = int(round((rem_secs - sec_int) * 1000))
        if millis >= 1000:
            millis = 999
        return f"{hours:02d}:{minutes:02d}:{sec_int:02d},{millis:03d}"
