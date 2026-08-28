"""Diagnostic Bundle Exporter.

Exports diagnostic_bundle_<run_id>.json containing full system environment context,
job states, exception stack traces, subprocess info, and log references without secrets.
"""

import json
import os
import platform
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from src.config.settings import AppSettings
from src.domain.models import Chapter, Job, ProductionRun, Project
from src.services.system_doctor import SystemDoctor


class DiagnosticBundleExporter:
    """Exports structured diagnostic_bundle_<run_id>.json upon pipeline errors."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.doctor = SystemDoctor(settings)

    def export_bundle(
        self,
        production_run: ProductionRun,
        project: Optional[Project] = None,
        chapter: Optional[Chapter] = None,
        job: Optional[Job] = None,
        exception: Optional[Exception] = None,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Export comprehensive diagnostic bundle JSON to disk."""
        run_id = production_run.id
        output_dir = self.settings.logs_dir / "diagnostics"
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle_file = output_dir / f"diagnostic_bundle_{run_id}.json"

        # System Doctor Environment Check
        sys_checks = self.doctor.run_foundation_checks()

        # Exception Traceback
        exc_info: Dict[str, Any] = {}
        if exception:
            exc_info = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc(),
            }

        bundle_data: Dict[str, Any] = {
            "run_id": run_id,
            "status": production_run.status.value if hasattr(production_run.status, "value") else str(production_run.status),
            "current_stage": production_run.current_stage.value if hasattr(production_run.current_stage, "value") else str(production_run.current_stage),
            "failure_reason": production_run.failure_reason,
            "environment": sys_checks,
            "project": {
                "id": project.id if project else None,
                "title": project.title if project else None,
                "type": project.project_type.value if project else None,
            },
            "chapter": {
                "id": chapter.id if chapter else None,
                "number": chapter.chapter_number if chapter else None,
                "sequence_index": chapter.sequence_index if chapter else None,
                "title": chapter.title if chapter else None,
            },
            "job": {
                "id": job.id if job else None,
                "type": job.job_type.value if job and hasattr(job.job_type, "value") else None,
                "status": job.status.value if job and hasattr(job.status, "value") else None,
                "error_message": job.error_message if job else None,
            },
            "exception": exc_info,
            "log_references": {
                "app_log": str(self.settings.app_log_path),
                "analysis_log": str(self.settings.logs_dir / "analysis.log"),
                "adaptation_log": str(self.settings.logs_dir / "adaptation.log"),
                "tts_log": str(self.settings.logs_dir / "tts.log"),
            },
            "extra": extra_info or {},
            "created_at": production_run.created_at,
        }

        bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")
        return bundle_file
