"""Versioned database migration runner.

Executes schema DDL migrations sequentially and records migration history.
"""

import sqlite3
from typing import List, Tuple
from src.database.engine import DatabaseEngine
from src.utilities.exceptions import MigrationError
from src.utilities.logging import get_logger

logger = get_logger()

# Versioned SQL migrations list
MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        "v1_initial_schema",
        """
        -- Schema Version Table
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );

        -- Projects Table
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            project_type TEXT NOT NULL,
            status TEXT NOT NULL,
            root_path TEXT NOT NULL,
            configuration_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- Sources Table
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            uri_or_path TEXT NOT NULL,
            content_hash TEXT NOT NULL DEFAULT '',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        -- Chapters Table
        CREATE TABLE IF NOT EXISTS chapters (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            chapter_number INTEGER NOT NULL,
            sequence_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            start_offset INTEGER NOT NULL DEFAULT 0,
            end_offset INTEGER NOT NULL DEFAULT 0,
            original_text TEXT NOT NULL,
            cleaned_text TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
        );

        -- Sections Table
        CREATE TABLE IF NOT EXISTS sections (
            id TEXT PRIMARY KEY,
            chapter_id TEXT NOT NULL,
            sequence_index INTEGER NOT NULL,
            section_type TEXT NOT NULL,
            start_offset INTEGER NOT NULL DEFAULT 0,
            end_offset INTEGER NOT NULL DEFAULT 0,
            text TEXT NOT NULL,
            content_hash TEXT NOT NULL DEFAULT '',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
        );

        -- Assets Table
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            content_hash TEXT NOT NULL DEFAULT '',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        -- Jobs Table
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            chapter_id TEXT,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0.0,
            attempt INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            input_hash TEXT NOT NULL DEFAULT '',
            output_asset_id TEXT,
            worker_id TEXT,
            error_code TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
            FOREIGN KEY (output_asset_id) REFERENCES assets(id) ON DELETE SET NULL
        );

        -- Production Runs Table
        CREATE TABLE IF NOT EXISTS production_runs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            plan_id TEXT,
            status TEXT NOT NULL,
            current_stage TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0.0,
            failure_reason TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        -- Performance Indexes
        CREATE INDEX IF NOT EXISTS idx_sources_project_id ON sources(project_id);
        CREATE INDEX IF NOT EXISTS idx_chapters_project_id ON chapters(project_id);
        CREATE INDEX IF NOT EXISTS idx_chapters_source_id ON chapters(source_id);
        CREATE INDEX IF NOT EXISTS idx_chapters_sequence_index ON chapters(sequence_index);
        CREATE INDEX IF NOT EXISTS idx_sections_chapter_id ON sections(chapter_id);
        CREATE INDEX IF NOT EXISTS idx_sections_sequence_index ON sections(sequence_index);
        CREATE INDEX IF NOT EXISTS idx_assets_project_id ON assets(project_id);
        CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_project_id ON jobs(project_id);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_production_runs_project_id ON production_runs(project_id);
        """
    )
]


class MigrationRunner:
    """Executes database schema migrations in order."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db_engine = db_engine

    def get_current_version(self) -> int:
        """Get highest applied schema version."""
        conn = self.db_engine.get_connection()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL);"
            )
            cursor = conn.execute("SELECT MAX(version) FROM schema_version;")
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0
        except sqlite3.Error as e:
            raise MigrationError(f"Failed to query schema version: {e}") from e

    def apply_migrations(self) -> int:
        """Apply all unapplied migrations sequentially."""
        current_version = self.get_current_version()
        applied_count = 0

        conn = self.db_engine.get_connection()

        for version, name, script in MIGRATIONS:
            if version > current_version:
                logger.info(f"Applying database migration v{version}: {name}")
                try:
                    with conn:
                        conn.executescript(script)
                        conn.execute(
                            "INSERT INTO schema_version (version, name, applied_at) VALUES (?, ?, datetime('now'));",
                            (version, name),
                        )
                    applied_count += 1
                except sqlite3.Error as e:
                    raise MigrationError(f"Migration v{version} ({name}) failed: {e}") from e

        # Perform Crash Recovery on startup (convert RUNNING jobs to INTERRUPTED)
        self._recover_interrupted_jobs()

        return applied_count

    def _recover_interrupted_jobs(self) -> None:
        """Recover jobs left in RUNNING status when process died."""
        conn = self.db_engine.get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE jobs SET status = 'INTERRUPTED', error_message = 'Process terminated while job was running' WHERE status = 'RUNNING';"
                )
                if cursor.rowcount > 0:
                    logger.warning(f"Crash recovery: converted {cursor.rowcount} stale RUNNING jobs to INTERRUPTED state.")
        except sqlite3.Error as e:
            logger.error(f"Error executing crash recovery for jobs: {e}")
