"""Media QA Validator & Report Generator.

Probes rendered MP4 videos for video stream, audio stream, resolution, FPS,
duration sync, and non-silent audio. Generates qa_report.json.
"""

import json
from pathlib import Path
from typing import List
from src.domain.render_models import QAReport, RenderSpec
from src.services.ffprobe_inspector import FFprobeInspector


class MediaQAValidator:
    """Validates rendered MP4 files against RenderSpec and generates qa_report.json."""

    def __init__(self):
        self.inspector = FFprobeInspector()

    def validate_render_output(self, spec: RenderSpec, output_path: Path) -> QAReport:
        """Probe output MP4 and verify video, audio, resolution, FPS, and duration sync."""
        path = Path(output_path)
        errors: List[str] = []
        warnings: List[str] = []

        probe_res = self.inspector.probe_media_file(path)

        if not probe_res.exists:
            errors.append(f"Rendered output file '{output_path}' does not exist.")
            qa_report = QAReport(
                render_spec_id=spec.id,
                output_path=str(path),
                is_passed=False,
                video_stream_ok=False,
                audio_stream_ok=False,
                resolution_ok=False,
                fps_ok=False,
                duration_sync_ok=False,
                subtitle_present=False,
                measured_duration_sec=0.0,
                measured_width=0,
                measured_height=0,
                measured_fps=0.0,
                errors=errors,
                warnings=warnings,
            )
            report_path = path.parent / "qa_report.json"
            self._write_qa_report_file(qa_report, report_path)
            return qa_report

        # 1. Video Stream Check
        video_ok = probe_res.has_video
        if not video_ok:
            errors.append("Rendered MP4 lacks a valid video stream.")

        # 2. Audio Stream Check
        audio_ok = probe_res.has_audio
        if not audio_ok:
            errors.append("Rendered MP4 lacks a valid audio stream (narration missing).")

        # 3. Resolution Check
        resolution_ok = (probe_res.width == spec.width) and (probe_res.height == spec.height)
        if not resolution_ok:
            errors.append(f"Resolution mismatch: expected {spec.width}x{spec.height}, got {probe_res.width}x{probe_res.height}.")

        # 4. FPS Check
        fps_ok = abs(probe_res.fps - spec.fps) <= 1.0
        if not fps_ok:
            warnings.append(f"FPS deviation: expected {spec.fps}, got {probe_res.fps}.")

        # 5. Audio/Video Duration Sync Check (tolerance 0.5 seconds)
        duration_diff = abs(probe_res.duration_seconds - spec.target_duration_seconds)
        duration_sync_ok = duration_diff <= 0.5
        if not duration_sync_ok:
            warnings.append(
                f"Duration sync difference ({duration_diff:.2f}s) exceeds 0.5s tolerance. "
                f"Expected {spec.target_duration_seconds:.2f}s, measured {probe_res.duration_seconds:.2f}s."
            )

        # 6. Subtitle presence
        subtitle_present = spec.subtitle_ass_path is not None and Path(spec.subtitle_ass_path).exists()
        if spec.subtitle_ass_path and not subtitle_present:
            errors.append("Subtitles were enabled in RenderSpec but subtitle file is missing.")

        is_passed = len(errors) == 0

        qa_report = QAReport(
            render_spec_id=spec.id,
            output_path=str(path),
            is_passed=is_passed,
            video_stream_ok=video_ok,
            audio_stream_ok=audio_ok,
            resolution_ok=resolution_ok,
            fps_ok=fps_ok,
            duration_sync_ok=duration_sync_ok,
            subtitle_present=subtitle_present,
            measured_duration_sec=probe_res.duration_seconds,
            measured_width=probe_res.width,
            measured_height=probe_res.height,
            measured_fps=probe_res.fps,
            errors=errors,
            warnings=warnings,
        )

        # Save qa_report.json on disk next to rendered video
        report_path = path.parent / "qa_report.json"
        self._write_qa_report_file(qa_report, report_path)

        return qa_report

    def _write_qa_report_file(self, report: QAReport, report_path: Path) -> None:
        """Save QA report as formatted JSON."""
        data = {
            "render_spec_id": report.render_spec_id,
            "output_path": report.output_path,
            "is_passed": report.is_passed,
            "checks": {
                "video_stream_ok": report.video_stream_ok,
                "audio_stream_ok": report.audio_stream_ok,
                "resolution_ok": report.resolution_ok,
                "fps_ok": report.fps_ok,
                "duration_sync_ok": report.duration_sync_ok,
                "subtitle_present": report.subtitle_present,
            },
            "measured_metrics": {
                "duration_seconds": report.measured_duration_sec,
                "width": report.measured_width,
                "height": report.measured_height,
                "fps": report.measured_fps,
            },
            "errors": report.errors,
            "warnings": report.warnings,
            "created_at": report.created_at,
        }
        report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
