"""Project Repository."""

import json
from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import Project, ProjectStatus, ProjectType
from src.utilities.exceptions import DatabaseError, ProjectNotFoundError


class ProjectRepository:
    """Repository for Project domain model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, project: Project) -> Project:
        """Create or update a Project."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO projects (id, title, project_type, status, root_path, configuration_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        project_type = excluded.project_type,
                        status = excluded.status,
                        root_path = excluded.root_path,
                        configuration_json = excluded.configuration_json,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        project.id,
                        project.title,
                        project.project_type.value,
                        project.status.value,
                        project.root_path,
                        json.dumps(project.configuration),
                        project.created_at,
                        project.updated_at,
                    ),
                )
            return project
        except Exception as e:
            raise DatabaseError(f"Failed to save project {project.id}: {e}") from e

    def get_by_id(self, project_id: str) -> Project:
        """Get project by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise ProjectNotFoundError(f"Project with ID '{project_id}' not found.")
        return Project(
            id=row["id"],
            title=row["title"],
            project_type=ProjectType(row["project_type"]),
            status=ProjectStatus(row["status"]),
            root_path=row["root_path"],
            configuration=json.loads(row["configuration_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_all(self) -> List[Project]:
        """List all projects sorted by updated_at desc."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC;")
        projects = []
        for row in cursor.fetchall():
            projects.append(
                Project(
                    id=row["id"],
                    title=row["title"],
                    project_type=ProjectType(row["project_type"]),
                    status=ProjectStatus(row["status"]),
                    root_path=row["root_path"],
                    configuration=json.loads(row["configuration_json"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return projects

    def count(self) -> int:
        """Get total project count."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM projects;")
        return cursor.fetchone()[0]

    def delete(self, project_id: str) -> bool:
        """Delete project by ID."""
        conn = self.db.get_connection()
        with conn:
            cursor = conn.execute("DELETE FROM projects WHERE id = ?;", (project_id,))
            return cursor.rowcount > 0
