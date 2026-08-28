"""Advanced SubStation Alpha (ASS) Subtitle Generator.

Generates ASS v4.00+ scripts featuring default center-center alignment (\\an5)
and preset styling profiles (YOUTUBE, SHORT_FORM, MOBILE_LARGE, CINEMATIC, etc.).
"""

from pathlib import Path
from typing import Dict, List
from src.domain.subtitle_models import SubtitleEvent, SubtitleStyleProfile


class ASSGenerator:
    """Generates ASS v4.00+ formatted subtitle files."""

    STYLE_PROFILES: Dict[SubtitleStyleProfile, Dict[str, str]] = {
        SubtitleStyleProfile.DEFAULT: {
            "Fontname": "Arial",
            "Fontsize": "24",
            "PrimaryColour": "&H00FFFFFF",  # White
            "OutlineColour": "&H00000000",  # Black outline
            "BackColour": "&H80000000",
            "Bold": "-1",
            "Italic": "0",
            "Outline": "2",
            "Shadow": "0",
            "Alignment": "5",  # \an5 Center-Center
            "MarginL": "10",
            "MarginR": "10",
            "MarginV": "10",
        },
        SubtitleStyleProfile.SHORT_FORM: {
            "Fontname": "Impact",
            "Fontsize": "36",
            "PrimaryColour": "&H0000FFFF",  # Yellow
            "OutlineColour": "&H00000000",
            "BackColour": "&H00000000",
            "Bold": "-1",
            "Italic": "0",
            "Outline": "3",
            "Shadow": "1",
            "Alignment": "5",  # \an5 Center-Center for Mobile Reels
            "MarginL": "20",
            "MarginR": "20",
            "MarginV": "20",
        },
        SubtitleStyleProfile.MOBILE_LARGE: {
            "Fontname": "Trebuchet MS",
            "Fontsize": "32",
            "PrimaryColour": "&H00FFFFFF",
            "OutlineColour": "&H00000000",
            "BackColour": "&H80000000",
            "Bold": "-1",
            "Italic": "0",
            "Outline": "3",
            "Shadow": "0",
            "Alignment": "5",  # \an5
            "MarginL": "15",
            "MarginR": "15",
            "MarginV": "15",
        },
        SubtitleStyleProfile.CINEMATIC: {
            "Fontname": "Times New Roman",
            "Fontsize": "20",
            "PrimaryColour": "&H00E0E0E0",
            "OutlineColour": "&H00000000",
            "BackColour": "&H80000000",
            "Bold": "0",
            "Italic": "1",
            "Outline": "1",
            "Shadow": "0",
            "Alignment": "2",  # Bottom-Center
            "MarginL": "30",
            "MarginR": "30",
            "MarginV": "20",
        },
    }

    def generate_ass(
        self,
        events: List[SubtitleEvent],
        output_path: Path,
        style_profile: SubtitleStyleProfile = SubtitleStyleProfile.DEFAULT,
        play_res_x: int = 1920,
        play_res_y: int = 1080,
    ) -> Path:
        """Generate ASS v4.00+ subtitle file on disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        style = self.STYLE_PROFILES.get(
            style_profile, self.STYLE_PROFILES[SubtitleStyleProfile.DEFAULT]
        )

        style_line = (
            f"Style: Default,{style['Fontname']},{style['Fontsize']},"
            f"{style['PrimaryColour']},&H000000FF,{style['OutlineColour']},"
            f"{style['BackColour']},{style['Bold']},{style['Italic']},0,0,100,100,0,0,"
            f"1,{style['Outline']},{style['Shadow']},{style['Alignment']},"
            f"{style['MarginL']},{style['MarginR']},{style['MarginV']},1"
        )

        header = f"""[Script Info]
Title: Studio-AI Narration Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        event_lines = []
        for ev in events:
            start_str = self._format_ass_timestamp(ev.start_time_seconds)
            end_str = self._format_ass_timestamp(ev.end_time_seconds)
            # Replace newlines with ASS \N line break
            formatted_text = ev.text.replace("\n", r"\N")
            event_lines.append(
                f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}"
            )

        full_ass_content = header + "\n".join(event_lines) + "\n"

        output_path.write_text(full_ass_content, encoding="utf-8")
        return output_path

    def _format_ass_timestamp(self, seconds: float) -> str:
        """Format seconds to ASS timestamp format `H:MM:SS.cs` (centiseconds)."""
        secs = max(0.0, seconds)
        hours = int(secs // 3600)
        minutes = int((secs % 3600) // 60)
        rem_secs = secs % 60
        sec_int = int(rem_secs)
        cs = int(round((rem_secs - sec_int) * 100))
        if cs >= 100:
            cs = 99
        return f"{hours}:{minutes:02d}:{sec_int:02d}.{cs:02d}"
