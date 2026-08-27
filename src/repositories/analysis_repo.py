"""Analysis Repository."""

import json
from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.ai_models import Analysis, AnalysisType, normalize_enum_value
from src.utilities.exceptions import DatabaseError, EntityNotFoundError


class AnalysisRepository:
    """Repository for Analysis model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def save(self, analysis: Analysis) -> Analysis:
        """Create or update an Analysis entity."""
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO analyses (
                        id, project_id, chapter_id, summary, characters_json, character_details_json,
                        locations_json, events_json, scenes_json, tone, mood, themes_json, dialogue_json,
                        narration_json, hooks_json, visual_opportunities_json, estimated_duration_seconds,
                        analysis_type, model_used, source_text_hash, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        summary = excluded.summary,
                        characters_json = excluded.characters_json,
                        character_details_json = excluded.character_details_json,
                        locations_json = excluded.locations_json,
                        events_json = excluded.events_json,
                        scenes_json = excluded.scenes_json,
                        tone = excluded.tone,
                        mood = excluded.mood,
                        themes_json = excluded.themes_json,
                        dialogue_json = excluded.dialogue_json,
                        narration_json = excluded.narration_json,
                        hooks_json = excluded.hooks_json,
                        visual_opportunities_json = excluded.visual_opportunities_json,
                        estimated_duration_seconds = excluded.estimated_duration_seconds,
                        analysis_type = excluded.analysis_type,
                        model_used = excluded.model_used,
                        source_text_hash = excluded.source_text_hash;
                    """,
                    (
                        analysis.id,
                        analysis.project_id,
                        analysis.chapter_id,
                        analysis.summary,
                        json.dumps(analysis.characters),
                        json.dumps(analysis.character_details),
                        json.dumps(analysis.locations),
                        json.dumps(analysis.events),
                        json.dumps(analysis.scenes),
                        analysis.tone,
                        analysis.mood,
                        json.dumps(analysis.themes),
                        json.dumps(analysis.dialogue),
                        json.dumps(analysis.narration),
                        json.dumps(analysis.hooks),
                        json.dumps(analysis.visual_opportunities),
                        analysis.estimated_duration_seconds,
                        normalize_enum_value(analysis.analysis_type, AnalysisType).value,
                        analysis.model_used,
                        analysis.source_text_hash,
                        analysis.created_at,
                    ),
                )
            return analysis
        except Exception as e:
            raise DatabaseError(f"Failed to save analysis {analysis.id}: {e}") from e

    def get_by_chapter(self, chapter_id: str) -> Optional[Analysis]:
        """Get latest analysis for a chapter."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM analyses WHERE chapter_id = ? ORDER BY created_at DESC LIMIT 1;",
            (chapter_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Analysis(
            id=row["id"],
            project_id=row["project_id"],
            chapter_id=row["chapter_id"],
            summary=row["summary"],
            characters=json.loads(row["characters_json"]),
            character_details=json.loads(row["character_details_json"]),
            locations=json.loads(row["locations_json"]),
            events=json.loads(row["events_json"]),
            scenes=json.loads(row["scenes_json"]),
            tone=row["tone"],
            mood=row["mood"],
            themes=json.loads(row["themes_json"]),
            dialogue=json.loads(row["dialogue_json"]),
            narration=json.loads(row["narration_json"]),
            hooks=json.loads(row["hooks_json"]),
            visual_opportunities=json.loads(row["visual_opportunities_json"]),
            estimated_duration_seconds=row["estimated_duration_seconds"],
            analysis_type=normalize_enum_value(row["analysis_type"], AnalysisType),
            model_used=row["model_used"],
            source_text_hash=row["source_text_hash"],
            created_at=row["created_at"],
        )
