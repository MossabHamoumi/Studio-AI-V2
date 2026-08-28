"""Local Asset Library Management Service."""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from src.domain.models import Asset, AssetStatus, AssetType
from src.repositories.asset_repo import AssetRepository
from src.services.ffprobe_inspector import FFprobeInspector
from src.utilities.exceptions import AssetNotFoundError


class AssetLibraryService:
    """Manages media asset registration, ffprobe metadata extraction, and missing asset recovery."""

    def __init__(self, asset_repo: AssetRepository):
        self.asset_repo = asset_repo
        self.inspector = FFprobeInspector()

    def register_media_asset(
        self,
        project_id: str,
        file_path: Path,
        asset_type: AssetType,
        category: str = "general",
        tags: Optional[List[str]] = None,
    ) -> Asset:
        """Register media asset in database and extract FFprobe metadata."""
        path = Path(file_path)
        probe_res = self.inspector.probe_media_file(path)

        status = AssetStatus.VALIDATED if probe_res.exists else AssetStatus.FAILED
        content_hash = ""
        size_bytes = 0

        if probe_res.exists:
            size_bytes = path.stat().st_size
            content_hash = hashlib.sha256(path.read_bytes()).hexdigest()

        metadata: Dict[str, Any] = {
            "category": category,
            "tags": tags or [],
            "duration_seconds": probe_res.duration_seconds,
            "resolution": f"{probe_res.width}x{probe_res.height}",
            "width": probe_res.width,
            "height": probe_res.height,
            "fps": probe_res.fps,
            "video_codec": probe_res.video_codec,
            "audio_codec": probe_res.audio_codec,
            "has_audio": probe_res.has_audio,
            "gameplay_audio_muted": True,  # Gameplay audio muted by default per specification
        }

        asset = Asset(
            project_id=project_id,
            asset_type=asset_type,
            path=str(path),
            size_bytes=size_bytes,
            content_hash=content_hash,
            metadata=metadata,
            status=status,
        )

        return self.asset_repo.register_asset(asset) if probe_res.exists else self.asset_repo.save(asset)

    def verify_asset_status(self, asset_id: str) -> Asset:
        """Verify if asset file exists on disk. Marks status MISSING if file was deleted."""
        asset = self.asset_repo.get_by_id(asset_id)
        path = Path(asset.path)

        if not path.exists():
            asset.status = AssetStatus.FAILED
            asset.metadata["missing"] = True
            return self.asset_repo.save(asset)

        asset.status = AssetStatus.VALIDATED
        asset.metadata["missing"] = False
        return self.asset_repo.save(asset)

    def calculate_gameplay_looping(
        self, gameplay_duration: float, target_narration_duration: float
    ) -> Tuple[int, float]:
        """Calculate required loops and duration for gameplay video to match narration duration."""
        if gameplay_duration <= 0:
            return 1, target_narration_duration

        loops = int(target_narration_duration // gameplay_duration) + 1
        return loops, round(target_narration_duration, 3)
