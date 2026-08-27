"""Workspace Manager.

Manages workspace folder layout and project manifest (project.json) serialization/sync.
"""

import json
from pathlib import Path
from typing import Any, Dict
from src.config.settings import AppSettings
from src.domain.models import Project
from src.utilities.exceptions import WorkspaceError


class WorkspaceManager:
    """Manages workspace directories and project.json manifest export."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    def initialize_project_workspace(self, project: Project) -> Path:
        """Create deterministic directory structure for a project."""
        pdir = self.settings.get_project_dir(project.id)
        project.root_path = str(pdir)
        self.write_manifest(project)
        return pdir

    def write_manifest(self, project: Project) -> Path:
        """Write project.json export manifest inside project directory."""
        if not project.root_path:
            pdir = self.settings.get_project_dir(project.id)
            project.root_path = str(pdir)
        else:
            pdir = Path(project.root_path)

        pdir.mkdir(parents=True, exist_ok=True)
        manifest_path = pdir / "project.json"

        manifest_data: Dict[str, Any] = {
            "id": project.id,
            "title": project.title,
            "project_type": project.project_type.value,
            "status": project.status.value,
            "root_path": project.root_path,
            "configuration": project.configuration,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)
            return manifest_path
        except Exception as e:
            raise WorkspaceError(f"Failed to write manifest at '{manifest_path}': {e}") from e
