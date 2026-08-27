"""Section Repository."""

import json
from typing import List
from src.database.engine import DatabaseEngine
from src.domain.models import Section, SectionType
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class SectionRepository:
    """Repository for Section model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, section: Section) -> Section:
        """Create or update a Section."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO sections (id, chapter_id, sequence_index, section_type, start_offset, end_offset, text, content_hash, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        sequence_index = excluded.sequence_index,
                        section_type = excluded.section_type,
                        start_offset = excluded.start_offset,
                        end_offset = excluded.end_offset,
                        text = excluded.text,
                        content_hash = excluded.content_hash,
                        metadata_json = excluded.metadata_json;
                    """,
                    (
                        section.id,
                        section.chapter_id,
                        section.sequence_index,
                        section.section_type.value,
                        section.start_offset,
                        section.end_offset,
                        section.text,
                        section.content_hash,
                        json.dumps(section.metadata),
                    ),
                )
            return section
        except Exception as e:
            raise DatabaseError(f"Failed to save section {section.id}: {e}") from e

    def list_by_chapter(self, chapter_id: str) -> List[Section]:
        """List all sections for a chapter ordered by sequence_index."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM sections WHERE chapter_id = ? ORDER BY sequence_index ASC;",
            (chapter_id,),
        )
        sections = []
        for row in cursor.fetchall():
            sections.append(
                Section(
                    id=row["id"],
                    chapter_id=row["chapter_id"],
                    sequence_index=row["sequence_index"],
                    section_type=SectionType(row["section_type"]),
                    start_offset=row["start_offset"],
                    end_offset=row["end_offset"],
                    text=row["text"],
                    content_hash=row["content_hash"],
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        return sections
