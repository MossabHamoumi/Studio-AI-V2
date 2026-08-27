"""Adaptation Repository."""

from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.ai_models import Adaptation, AdaptationStatus, normalize_enum_value
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class AdaptationRepository:
    """Repository for Adaptation model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, adaptation: Adaptation) -> Adaptation:
        """Create or update an Adaptation entity."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO adaptations (
                        id, project_id, chapter_id, adapted_text, source_text_hash,
                        model_used, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        adapted_text = excluded.adapted_text,
                        status = excluded.status,
                        model_used = excluded.model_used,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        adaptation.id,
                        adaptation.project_id,
                        adaptation.chapter_id,
                        adaptation.adapted_text,
                        adaptation.source_text_hash,
                        adaptation.model_used,
                        normalize_enum_value(adaptation.status, AdaptationStatus).value,
                        adaptation.created_at,
                        adaptation.updated_at,
                    ),
                )
            return adaptation
        except Exception as e:
            raise DatabaseError(f"Failed to save adaptation {adaptation.id}: {e}") from e

    def get_by_chapter(self, chapter_id: str) -> Optional[Adaptation]:
        """Get latest adaptation for a chapter."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM adaptations WHERE chapter_id = ? ORDER BY updated_at DESC LIMIT 1;",
            (chapter_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Adaptation(
            id=row["id"],
            project_id=row["project_id"],
            chapter_id=row["chapter_id"],
            adapted_text=row["adapted_text"],
            source_text_hash=row["source_text_hash"],
            model_used=row["model_used"],
            status=normalize_enum_value(row["status"], AdaptationStatus),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_accepted_by_chapter(self, chapter_id: str) -> Optional[Adaptation]:
        """Get accepted adaptation for a chapter."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM adaptations WHERE chapter_id = ? AND status = 'ACCEPTED' LIMIT 1;",
            (chapter_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Adaptation(
            id=row["id"],
            project_id=row["project_id"],
            chapter_id=row["chapter_id"],
            adapted_text=row["adapted_text"],
            source_text_hash=row["source_text_hash"],
            model_used=row["model_used"],
            status=normalize_enum_value(row["status"], AdaptationStatus),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
