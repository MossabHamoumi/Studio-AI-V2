"""Chapter Repository."""

from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import Chapter, ChapterStatus
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class ChapterRepository:
    """Repository for Chapter model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, chapter: Chapter) -> Chapter:
        """Create or update a Chapter."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO chapters (
                        id, project_id, source_id, chapter_number, sequence_index, title,
                        start_offset, end_offset, original_text, cleaned_text, content_hash,
                        status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        chapter_number = excluded.chapter_number,
                        sequence_index = excluded.sequence_index,
                        title = excluded.title,
                        start_offset = excluded.start_offset,
                        end_offset = excluded.end_offset,
                        original_text = excluded.original_text,
                        cleaned_text = excluded.cleaned_text,
                        content_hash = excluded.content_hash,
                        status = excluded.status,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        chapter.id,
                        chapter.project_id,
                        chapter.source_id,
                        chapter.chapter_number,
                        chapter.sequence_index,
                        chapter.title,
                        chapter.start_offset,
                        chapter.end_offset,
                        chapter.original_text,
                        chapter.cleaned_text,
                        chapter.content_hash,
                        chapter.status.value,
                        chapter.created_at,
                        chapter.updated_at,
                    ),
                )
            return chapter
        except Exception as e:
            raise DatabaseError(f"Failed to save chapter {chapter.id}: {e}") from e

    def get_by_id(self, chapter_id: str) -> Chapter:
        """Get chapter by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM chapters WHERE id = ?;", (chapter_id,))
        row = cursor.fetchone()
        if not row:
            raise EntityNotFoundError(f"Chapter with ID '{chapter_id}' not found.")
        return Chapter(
            id=row["id"],
            project_id=row["project_id"],
            source_id=row["source_id"],
            chapter_number=row["chapter_number"],
            sequence_index=row["sequence_index"],
            title=row["title"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            original_text=row["original_text"],
            cleaned_text=row["cleaned_text"],
            content_hash=row["content_hash"],
            status=ChapterStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_by_project(self, project_id: str) -> List[Chapter]:
        """List chapters for a project ordered strictly by sequence_index."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM chapters WHERE project_id = ? ORDER BY sequence_index ASC;",
            (project_id,),
        )
        chapters = []
        for row in cursor.fetchall():
            chapters.append(
                Chapter(
                    id=row["id"],
                    project_id=row["project_id"],
                    source_id=row["source_id"],
                    chapter_number=row["chapter_number"],
                    sequence_index=row["sequence_index"],
                    title=row["title"],
                    start_offset=row["start_offset"],
                    end_offset=row["end_offset"],
                    original_text=row["original_text"],
                    cleaned_text=row["cleaned_text"],
                    content_hash=row["content_hash"],
                    status=ChapterStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return chapters
