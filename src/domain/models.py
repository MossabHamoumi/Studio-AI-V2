"""Core domain entity models for Studio-AI.

All entities use stable UUID strings as their primary key identity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


def generate_uuid() -> str:
    """Generate a stable string UUID v4."""
    return str(uuid.uuid4())


def current_utc_timestamp() -> str:
    """Get ISO 8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class ProjectType(str, Enum):
    NOVEL = "NOVEL"
    SHORT_STORY = "SHORT_STORY"
    ORIGINAL_STORY = "ORIGINAL_STORY"
    HORROR_STORY = "HORROR_STORY"
    PHONE_CALL = "PHONE_CALL"
    DIALOGUE = "DIALOGUE"
    REDDIT_STYLE = "REDDIT_STYLE"
    PODCAST = "PODCAST"
    GAMEPLAY_STORY = "GAMEPLAY_STORY"
    CUSTOM = "CUSTOM"


class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SourceType(str, Enum):
    TXT_FILE = "TXT_FILE"
    PASTED_TEXT = "PASTED_TEXT"
    IDEA_PROMPT = "IDEA_PROMPT"
    WEB_DISCOVERY = "WEB_DISCOVERY"


class SourceStatus(str, Enum):
    RAW = "RAW"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    ERROR = "ERROR"


class ChapterStatus(str, Enum):
    PENDING = "PENDING"
    CLEANED = "CLEANED"
    ANALYZED = "ANALYZED"
    NARRATED = "NARRATED"
    RENDERED = "RENDERED"
    COMPLETED = "COMPLETED"


class SectionType(str, Enum):
    NARRATION = "NARRATION"
    DIALOGUE = "DIALOGUE"
    SCENE = "SCENE"
    HOOK = "HOOK"
    INTRO = "INTRO"
    OUTRO = "OUTRO"
    UNKNOWN = "UNKNOWN"


class AssetType(str, Enum):
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    SUBTITLE = "SUBTITLE"
    THUMBNAIL = "THUMBNAIL"
    GAMEPLAY = "GAMEPLAY"
    TEXT = "TEXT"
    OTHER = "OTHER"


class AssetStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class JobType(str, Enum):
    IMPORT_SOURCE = "IMPORT_SOURCE"
    SPLIT_CHAPTERS = "SPLIT_CHAPTERS"
    ANALYZE_STORY = "ANALYZE_STORY"
    ADAPT_SCRIPT = "ADAPT_SCRIPT"
    GENERATE_TTS = "GENERATE_TTS"
    GENERATE_SUBTITLES = "GENERATE_SUBTITLES"
    PREPARE_VISUALS = "PREPARE_VISUALS"
    RENDER_VIDEO = "RENDER_VIDEO"
    MEDIA_QA = "MEDIA_QA"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"


class StageName(str, Enum):
    ANALYSIS = "ANALYSIS"
    ADAPTATION = "ADAPTATION"
    NARRATION = "NARRATION"
    SUBTITLES = "SUBTITLES"
    VISUALS = "VISUALS"
    RENDER = "RENDER"
    QA = "QA"


class ProductionRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Project:
    title: str
    project_type: ProjectType = ProjectType.NOVEL
    status: ProjectStatus = ProjectStatus.ACTIVE
    root_path: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    updated_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class Source:
    project_id: str
    source_type: SourceType = SourceType.TXT_FILE
    uri_or_path: str = ""
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: SourceStatus = SourceStatus.RAW
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    updated_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class Chapter:
    project_id: str
    source_id: str
    chapter_number: int
    sequence_index: int
    title: str
    start_offset: int
    end_offset: int
    original_text: str
    cleaned_text: str = ""
    content_hash: str = ""
    status: ChapterStatus = ChapterStatus.PENDING
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    updated_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class Section:
    chapter_id: str
    sequence_index: int
    section_type: SectionType = SectionType.NARRATION
    start_offset: int = 0
    end_offset: int = 0
    text: str = ""
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=generate_uuid)


@dataclass
class Asset:
    project_id: str
    asset_type: AssetType
    path: str
    size_bytes: int = 0
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AssetStatus = AssetStatus.PENDING
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    updated_at: str = field(default_factory=current_utc_timestamp)


@dataclass
class Job:
    project_id: str
    job_type: JobType
    chapter_id: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    attempt: int = 0
    max_attempts: int = 3
    input_hash: str = ""
    output_asset_id: Optional[str] = None
    worker_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ProductionRun:
    project_id: str
    plan_id: Optional[str] = None
    status: ProductionRunStatus = ProductionRunStatus.PENDING
    current_stage: StageName = StageName.ANALYSIS
    progress: float = 0.0
    failure_reason: Optional[str] = None
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_utc_timestamp)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
