"""Idempotency Signature Foundation."""

import hashlib
import json
from typing import Any, Dict, Optional
from src.domain.models import JobType


def compute_job_signature(
    project_id: str,
    job_type: JobType,
    input_hash: str,
    chapter_id: Optional[str] = None,
    configuration: Optional[Dict[str, Any]] = None,
    pipeline_version: str = "1.0",
) -> str:
    """Compute a deterministic SHA-256 work signature for a job.

    Enables reuse of TTS audio, story analysis, and render outputs when inputs match.
    """
    config_str = json.dumps(configuration or {}, sort_keys=True)
    raw_key = f"{project_id}|{chapter_id or ''}|{job_type.value}|{input_hash}|{config_str}|{pipeline_version}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
