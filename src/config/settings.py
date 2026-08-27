"""Configuration settings for Studio-AI."""

import os
from pathlib import Path
from typing import Optional


class AppSettings:
    """Application configuration container."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        if workspace_dir is None:
            user_home = Path.home()
            self.workspace_dir = user_home / ".studio-ai"
        else:
            self.workspace_dir = Path(workspace_dir)

        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.workspace_dir / "studio_ai.db"
        self.projects_dir = self.workspace_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = self.workspace_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.app_log_path = self.logs_dir / "app.log"

    def get_project_dir(self, project_id: str) -> Path:
        """Get or create project directory layout."""
        pdir = self.projects_dir / project_id
        for subdir in ["sources", "assets", "chapters", "outputs", "cache", "logs"]:
            (pdir / subdir).mkdir(parents=True, exist_ok=True)
        return pdir
