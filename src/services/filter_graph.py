"""FFmpeg Complex FilterGraph Builder.

Constructs explicit FFmpeg filter graphs for static image scaling/crop, gameplay video looping,
title card overlays, and ASS subtitle burn-in filters.
"""

from pathlib import Path
from typing import List, Tuple
from src.domain.render_models import RenderSpec


class FilterGraphBuilder:
    """Constructs explicit FFmpeg complex filter graphs."""

    def build_filter_graph(self, spec: RenderSpec) -> Tuple[str, str, str]:
        """Build complex filtergraph string and return (filter_str, video_stream_map, audio_stream_map)."""
        video_filters: List[str] = []

        # 1. Scale and Crop to Target Aspect Ratio
        scale_crop = (
            f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=increase,"
            f"crop={spec.width}:{spec.height}"
        )
        video_filters.append(scale_crop)

        # 2. Title Card Overlay (if specified)
        if spec.title_card and spec.title_card.title:
            safe_title = spec.title_card.title.replace("'", "").replace(":", r"\:")
            tc_fade = (
                f"drawtext=text='{safe_title}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:"
                f"enable='between(t,0,{spec.title_card.hold_sec})'"
            )
            video_filters.append(tc_fade)

        # 3. ASS Subtitle Burn-In Filter (if enabled)
        if spec.subtitle_ass_path:
            ass_path_str = Path(spec.subtitle_ass_path).as_posix().replace("'", r"\'").replace(":", r"\:")
            video_filters.append(f"ass='{ass_path_str}'")

        # Combine video filters chain
        full_video_filter = ",".join(video_filters)
        filter_complex = f"[0:v]{full_video_filter}[v]"

        # Stream 1 narration audio stream map is '1:a'
        return filter_complex, "[v]", "1:a"
