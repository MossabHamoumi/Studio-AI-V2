"""Job Repository."""

from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import Job, JobStatus, JobType
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class JobRepository:
    """Repository for Job model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, job: Job) -> Job:
        """Create or update a Job."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO jobs (
                        id, project_id, chapter_id, job_type, status, progress, attempt, max_attempts,
                        input_hash, output_asset_id, worker_id, error_code, error_message, created_at,
                        started_at, completed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        progress = excluded.progress,
                        attempt = excluded.attempt,
                        output_asset_id = excluded.output_asset_id,
                        worker_id = excluded.worker_id,
                        error_code = excluded.error_code,
                        error_message = excluded.error_message,
                        started_at = excluded.started_at,
                        completed_at = excluded.completed_at;
                    """,
                    (
                        job.id,
                        job.project_id,
                        job.chapter_id,
                        job.job_type.value,
                        job.status.value,
                        job.progress,
                        job.attempt,
                        job.max_attempts,
                        job.input_hash,
                        job.output_asset_id,
                        job.worker_id,
                        job.error_code,
                        job.error_message,
                        job.created_at,
                        job.started_at,
                        job.completed_at,
                    ),
                )
            return job
        except Exception as e:
            raise DatabaseError(f"Failed to save job {job.id}: {e}") from e

    def get_by_id(self, job_id: str) -> Job:
        """Get job by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?;", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise EntityNotFoundError(f"Job with ID '{job_id}' not found.")
        return Job(
            id=row["id"],
            project_id=row["project_id"],
            chapter_id=row["chapter_id"],
            job_type=JobType(row["job_type"]),
            status=JobStatus(row["status"]),
            progress=row["progress"],
            attempt=row["attempt"],
            max_attempts=row["max_attempts"],
            input_hash=row["input_hash"],
            output_asset_id=row["output_asset_id"],
            worker_id=row["worker_id"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def list_by_project(self, project_id: str) -> List[Job]:
        """List jobs for a project."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at ASC;",
            (project_id,),
        )
        jobs = []
        for row in cursor.fetchall():
            jobs.append(
                Job(
                    id=row["id"],
                    project_id=row["project_id"],
                    chapter_id=row["chapter_id"],
                    job_type=JobType(row["job_type"]),
                    status=JobStatus(row["status"]),
                    progress=row["progress"],
                    attempt=row["attempt"],
                    max_attempts=row["max_attempts"],
                    input_hash=row["input_hash"],
                    output_asset_id=row["output_asset_id"],
                    worker_id=row["worker_id"],
                    error_code=row["error_code"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                )
            )
        return jobs
