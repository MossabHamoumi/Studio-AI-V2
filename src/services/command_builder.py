"""FFmpeg Command Line Builder.

Assembles explicit FFmpeg commands with stream mapping (-map [v] -map [a]),
safe stdin handling (-nostdin -progress pipe:1), and H.264/AAC encoding parameters.
"""

from pathlib import Path
from typing import List
from src.domain.render_models import RenderSpec
from src.domain.visual_models import VisualMode
from src.services.filter_graph import FilterGraphBuilder


class FFmpegCommandBuilder:
    """Builds safe, explicit FFmpeg command argument lists."""

    def __init__(self):
        self.filter_builder = FilterGraphBuilder()

    def build_command(self, spec: RenderSpec) -> List[str]:
        """Build argument list for ffmpeg subprocess execution."""
        cmd: List[str] = ["ffmpeg", "-y", "-nostdin", "-progress", "pipe:1"]

        # Input 0: Visual Source (Image or Video)
        if spec.visual_mode == VisualMode.GAMEPLAY and spec.gameplay_video_path:
            cmd.extend(["-stream_loop", "-1", "-i", str(spec.gameplay_video_path)])
        elif spec.background_image_path:
            cmd.extend([
                "-loop", "1",
                "-t", str(spec.target_duration_seconds),
                "-i", str(spec.background_image_path),
            ])
        else:
            # Fallback color video input
            cmd.extend([
                "-f", "lavfi",
                "-i", f"color=c=black:s={spec.width}x{spec.height}:d={spec.target_duration_seconds}",
            ])

        # Input 1: Narration Audio Source
        cmd.extend(["-i", str(spec.narration_audio_path)])

        # FilterGraph Construction
        filter_str, v_map, a_map = self.filter_builder.build_filter_graph(spec)

        cmd.extend(["-filter_complex", filter_str])
        cmd.extend(["-map", v_map, "-map", a_map])

        # Encoding Parameters
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", str(spec.fps),
            "-c:a", "aac",
            "-b:a", "192000",
            "-shortest",
            str(spec.output_path),
        ])

        return cmd
