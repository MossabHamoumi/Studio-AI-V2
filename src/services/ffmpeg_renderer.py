"""FFmpeg Subprocess Renderer.

Executes FFmpeg rendering processes safely with progress monitoring,
cancellation support, and stdin=DEVNULL handling.
"""

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Callable, List, Optional
from src.domain.render_models import RenderSpec
from src.services.command_builder import FFmpegCommandBuilder
from src.utilities.exceptions import StudioAIError
from src.utilities.logging import get_logger

logger = get_logger()


class FFmpegRenderer:
    """Executes FFmpeg process and monitors render progress."""

    def __init__(self):
        self.cmd_builder = FFmpegCommandBuilder()
        self._current_process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def render(
        self,
        spec: RenderSpec,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Path:
        """Execute FFmpeg render command to produce output MP4 file."""
        output_path = Path(spec.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = self.cmd_builder.build_command(spec)
        logger.info(f"Executing FFmpeg Render Command: {' '.join(cmd)}")

        self._is_cancelled = False
        stderr_logs: List[str] = []

        try:
            # Combine stderr into stdout to prevent pipe buffer deadlocks
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._current_process = process

            # Monitor combined progress pipe
            if process.stdout:
                for line in process.stdout:
                    if self._is_cancelled:
                        break
                    line_str = line.strip()
                    stderr_logs.append(line_str)
                    if line_str.startswith("out_time_us="):
                        try:
                            us = float(line_str.split("=")[1])
                            curr_sec = us / 1_000_000.0
                            if spec.target_duration_seconds > 0 and progress_callback:
                                prog = min(1.0, curr_sec / spec.target_duration_seconds)
                                progress_callback(prog)
                        except (ValueError, IndexError):
                            pass

            process.wait()

            if self._is_cancelled:
                if output_path.exists():
                    output_path.unlink()
                raise StudioAIError("Render process was cancelled by user.")

            if process.returncode != 0:
                err_tail = "\n".join(stderr_logs[-20:])
                logger.error(f"FFmpeg render failed with return code {process.returncode}: {err_tail}")
                raise StudioAIError(f"FFmpeg rendering failed: {err_tail}")

            if not output_path.exists() or output_path.stat().st_size <= 1000:
                raise StudioAIError(f"FFmpeg output file '{output_path}' was not generated or is empty.")

            logger.info(f"FFmpeg Render SUCCESS: Output generated at {output_path}")
            return output_path

        except Exception as e:
            if self._is_cancelled:
                raise StudioAIError("Render process cancelled.") from e
            raise StudioAIError(f"Render execution error: {e}") from e
        finally:
            self._current_process = None

    def cancel_render(self) -> None:
        """Safely terminate active FFmpeg render process."""
        self._is_cancelled = True
        if self._current_process and self._current_process.poll() is None:
            logger.warning("Cancelling active FFmpeg render process...")
            try:
                self._current_process.terminate()
                time.sleep(0.2)
                if self._current_process.poll() is None:
                    self._current_process.kill()
            except Exception as e:
                logger.error(f"Error terminating FFmpeg process: {e}")
