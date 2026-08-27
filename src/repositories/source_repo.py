"""Source Repository."""

import json
from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import Source, SourceStatus, SourceType
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class SourceRepository:
    """Repository for Source model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, source: Source) -> Source:
        """Create or update a Source."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO sources (id, project_id, source_type, uri_or_path, content_hash, metadata_json, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        source_type = excluded.source_type,
                        uri_or_path = excluded.uri_or_path,
                        content_hash = excluded.content_hash,
                        metadata_json = excluded.metadata_json,
                        status = excluded.status,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        source.id,
                        source.project_id,
                        source.source_type.value,
                        source.uri_or_path,
                        source.content_hash,
                        json.dumps(source.metadata),
                        source.status.value,
                        source.created_at,
                        source.updated_at,
                    ),
                )
            return source
        except Exception as e:
            raise DatabaseError(f"Failed to save source {source.id}: {e}") from e

    def get_by_id(self, source_id: str) -> Source:
        """Get source by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM sources WHERE id = ?;", (source_id,))
        row = cursor.fetchone()
        if not row:
            raise EntityNotFoundError(f"Source with ID '{source_id}' not found.")
        return Source(
            id=row["id"],
            project_id=row["project_id"],
            source_type=SourceType(row["source_type"]),
            uri_or_path=row["uri_or_path"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
            status=SourceStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_by_project(self, project_id: str) -> List[Source]:
        """List all sources for a project."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM sources WHERE project_id = ? ORDER BY created_at ASC;",
            (project_id,),
        )
        sources = []
        for row in cursor.fetchall():
            sources.append(
                Source(
                    id=row["id"],
                    project_id=row["project_id"],
                    source_type=SourceType(row["source_type"]),
                    uri_or_path=row["uri_or_path"],
                    content_hash=row["content_hash"],
                    metadata=json.loads(row["metadata_json"]),
                    status=SourceStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return sources
