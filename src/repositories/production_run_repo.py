"""ProductionRun Repository."""

from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import ProductionRun, ProductionRunStatus, StageName
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class ProductionRunRepository:
    """Repository for ProductionRun model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, run: ProductionRun) -> ProductionRun:
        """Create or update a ProductionRun."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO production_runs (id, project_id, plan_id, status, current_stage, progress, failure_reason, created_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        current_stage = excluded.current_stage,
                        progress = excluded.progress,
                        failure_reason = excluded.failure_reason,
                        started_at = excluded.started_at,
                        completed_at = excluded.completed_at;
                    """,
                    (
                        run.id,
                        run.project_id,
                        run.plan_id,
                        run.status.value,
                        run.current_stage.value,
                        run.progress,
                        run.failure_reason,
                        run.created_at,
                        run.started_at,
                        run.completed_at,
                    ),
                )
            return run
        except Exception as e:
            raise DatabaseError(f"Failed to save production run {run.id}: {e}") from e

    def get_by_id(self, run_id: str) -> ProductionRun:
        """Get production run by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM production_runs WHERE id = ?;", (run_id,))
        row = cursor.fetchone()
        if not row:
            raise EntityNotFoundError(f"ProductionRun with ID '{run_id}' not found.")
        return ProductionRun(
            id=row["id"],
            project_id=row["project_id"],
            plan_id=row["plan_id"],
            status=ProductionRunStatus(row["status"]),
            current_stage=StageName(row["current_stage"]),
            progress=row["progress"],
            failure_reason=row["failure_reason"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def list_by_project(self, project_id: str) -> List[ProductionRun]:
        """List production runs for a project."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM production_runs WHERE project_id = ? ORDER BY created_at DESC;",
            (project_id,),
        )
        runs = []
        for row in cursor.fetchall():
            runs.append(
                ProductionRun(
                    id=row["id"],
                    project_id=row["project_id"],
                    plan_id=row["plan_id"],
                    status=ProductionRunStatus(row["status"]),
                    current_stage=StageName(row["current_stage"]),
                    progress=row["progress"],
                    failure_reason=row["failure_reason"],
                    created_at=row["created_at"],
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                )
            )
        return runs
