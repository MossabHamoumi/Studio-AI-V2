"""Dedicated Subtitle Validator.

Validates subtitle event timing boundaries, order, overlap prevention, non-emptiness,
and alignment with total audio duration.
"""

from typing import List
from src.domain.subtitle_models import SubtitleEvent, SubtitleValidationResult


class SubtitleValidator:
    """Validates subtitle events for strict timing, non-overlap, and duration alignment."""

    def validate_subtitle_events(
        self, events: List[SubtitleEvent], max_audio_duration: float
    ) -> SubtitleValidationResult:
        """Validate list of subtitle events."""
        errors: List[str] = []
        warnings: List[str] = []

        if not events:
            return SubtitleValidationResult(
                is_valid=False,
                total_events=0,
                errors=["Subtitle event list is empty."],
            )

        prev_end = 0.0

        for idx, ev in enumerate(events):
            # 1. Non-empty text
            if not ev.text or not ev.text.strip():
                errors.append(f"Event #{idx}: Text is empty.")

            # 2. Start time non-negative
            if ev.start_time_seconds < -0.001:
                errors.append(f"Event #{idx}: Start time ({ev.start_time_seconds:.3f}s) is negative.")

            # 3. End time strictly after start time
            if ev.end_time_seconds <= ev.start_time_seconds + 0.001:
                errors.append(
                    f"Event #{idx}: End time ({ev.end_time_seconds:.3f}s) <= Start time ({ev.start_time_seconds:.3f}s)."
                )

            # 4. Overlap check with previous event (tolerance epsilon = 0.002s for floating point rounding)
            if idx > 0 and ev.start_time_seconds < prev_end - 0.002:
                errors.append(
                    f"Event #{idx}: Overlaps with previous event. Start ({ev.start_time_seconds:.3f}s) < Previous End ({prev_end:.3f}s)."
                )

            # 5. Total audio duration boundary check
            if ev.end_time_seconds > max_audio_duration + 0.1:
                warnings.append(
                    f"Event #{idx}: End time ({ev.end_time_seconds:.3f}s) exceeds total audio duration ({max_audio_duration:.3f}s)."
                )

            prev_end = ev.end_time_seconds

        is_valid = len(errors) == 0

        return SubtitleValidationResult(
            is_valid=is_valid,
            total_events=len(events),
            errors=errors,
            warnings=warnings,
        )
