"""Asset Repository."""

import json
from pathlib import Path
from typing import List, Optional
from src.database.engine import DatabaseEngine
from src.domain.models import Asset, AssetStatus, AssetType
from src.utilities.exceptions import AssetNotFoundError, DatabaseError, ValidationError


class AssetRepository:
    """Repository for Asset model."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def register_asset(self, asset: Asset) -> Asset:
        """Register and validate an asset file.

        Verifies that file exists on disk and size > 0 before registration.
        """
        file_path = Path(asset.path)
        if not file_path.exists():
            raise AssetNotFoundError(f"Asset path '{asset.path}' does not exist on disk.")

        file_size = file_path.stat().st_size
        if file_size <= 0:
            raise ValidationError(f"Asset file '{asset.path}' is empty (size <= 0 bytes).")

        asset.size_bytes = file_size
        asset.status = AssetStatus.VALIDATED

        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO assets (id, project_id, asset_type, path, size_bytes, content_hash, metadata_json, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        asset_type = excluded.asset_type,
                        path = excluded.path,
                        size_bytes = excluded.size_bytes,
                        content_hash = excluded.content_hash,
                        metadata_json = excluded.metadata_json,
                        status = excluded.status,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        asset.id,
                        asset.project_id,
                        asset.asset_type.value,
                        asset.path,
                        asset.size_bytes,
                        asset.content_hash,
                        json.dumps(asset.metadata),
                        asset.status.value,
                        asset.created_at,
                        asset.updated_at,
                    ),
                )
            return asset
        except Exception as e:
            raise DatabaseError(f"Failed to register asset {asset.id}: {e}") from e

    def get_by_id(self, asset_id: str) -> Asset:
        """Get asset by ID."""
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
        row = cursor.fetchone()
        if not row:
            raise AssetNotFoundError(f"Asset with ID '{asset_id}' not found.")
        return Asset(
            id=row["id"],
            project_id=row["project_id"],
            asset_type=AssetType(row["asset_type"]),
            path=row["path"],
            size_bytes=row["size_bytes"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
            status=AssetStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_by_project(self, project_id: str) -> List[Asset]:
        """List assets for a project."""
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM assets WHERE project_id = ? ORDER BY created_at DESC;",
            (project_id,),
        )
        assets = []
        for row in cursor.fetchall():
            assets.append(
                Asset(
                    id=row["id"],
                    project_id=row["project_id"],
                    asset_type=AssetType(row["asset_type"]),
                    path=row["path"],
                    size_bytes=row["size_bytes"],
                    content_hash=row["content_hash"],
                    metadata=json.loads(row["metadata_json"]),
                    status=AssetStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return assets
