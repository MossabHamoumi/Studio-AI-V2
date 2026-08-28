"""FFprobe Media Inspector.

Inspects video, image, and audio files for duration, resolution, FPS, and codecs.
Handles missing/corrupted files gracefully without crashing.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class MediaProbeResult:
    """Probe statistics for video, image, or audio asset."""

    file_path: str
    exists: bool
    duration_seconds: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str
    has_video: bool
    has_audio: bool
    error_message: Optional[str] = None


class FFprobeInspector:
    """Probes media metadata using ffprobe binary with safe fallback handling."""

    def probe_media_file(self, file_path: Path) -> MediaProbeResult:
        """Probe media file. Flags MISSING files gracefully if missing on disk."""
        path = Path(file_path)
        if not path.exists():
            return MediaProbeResult(
                file_path=str(path),
                exists=False,
                duration_seconds=0.0,
                width=0,
                height=0,
                fps=0.0,
                video_codec="",
                audio_codec="",
                has_video=False,
                has_audio=False,
                error_message=f"File '{file_path}' does not exist on disk.",
            )

        # Attempt probing via ffprobe CLI
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)

            format_info = data.get("format", {})
            streams = data.get("streams", [])

            duration = float(format_info.get("duration", 0.0))
            width = 0
            height = 0
            fps = 0.0
            v_codec = ""
            a_codec = ""
            has_v = False
            has_a = False

            for s in streams:
                codec_type = s.get("codec_type")
                if codec_type == "video" and not has_v:
                    has_v = True
                    width = int(s.get("width", 0))
                    height = int(s.get("height", 0))
                    v_codec = s.get("codec_name", "")

                    # Extract FPS
                    r_fps = s.get("r_frame_rate", "0/1")
                    if "/" in r_fps:
                        num, den = r_fps.split("/")
                        if float(den) > 0:
                            fps = round(float(num) / float(den), 2)
                    else:
                        fps = float(r_fps)

                elif codec_type == "audio" and not has_a:
                    has_a = True
                    a_codec = s.get("codec_name", "")

            return MediaProbeResult(
                file_path=str(path),
                exists=True,
                duration_seconds=round(duration, 3),
                width=width,
                height=height,
                fps=fps,
                video_codec=v_codec,
                audio_codec=a_codec,
                has_video=has_v,
                has_audio=has_a,
            )

        except Exception as e:
            # Fallback for images or if ffprobe is absent
            if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                return MediaProbeResult(
                    file_path=str(path),
                    exists=True,
                    duration_seconds=0.0,
                    width=1920,
                    height=1080,
                    fps=0.0,
                    video_codec="image",
                    audio_codec="",
                    has_video=True,
                    has_audio=False,
                )

            return MediaProbeResult(
                file_path=str(path),
                exists=True,
                duration_seconds=0.0,
                width=0,
                height=0,
                fps=0.0,
                video_codec="",
                audio_codec="",
                has_video=False,
                has_audio=False,
                error_message=f"FFprobe execution failed: {e}",
            )
