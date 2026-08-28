"""Single Application Session Context for Studio-AI.

Guarantees one authoritative active project/chapter state across all desktop UI views.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from src.domain.models import StageName


@dataclass
class SessionContext:
    """Shared application session state container."""

    active_project_id: Optional[str] = None
    active_source_id: Optional[str] = None
    active_chapter_id: Optional[str] = None
    selected_chapter_ids: List[str] = field(default_factory=list)
    current_stage: StageName = StageName.ANALYSIS
    current_production_plan_id: Optional[str] = None
    current_production_run_id: Optional[str] = None

    _listeners: List[Callable[["SessionContext"], None]] = field(default_factory=list)

    def add_listener(self, callback: Callable[["SessionContext"], None]) -> None:
        """Register a callback listener when session context updates."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def notify_listeners(self) -> None:
        """Notify all registered UI views of state changes."""
        for cb in self._listeners:
            try:
                cb(self)
            except Exception:
                pass

    def set_active_project(self, project_id: str) -> None:
        """Set active project and notify listeners."""
        self.active_project_id = project_id
        self.notify_listeners()

    def set_active_chapter(self, chapter_id: str) -> None:
        """Set active chapter and notify listeners."""
        self.active_chapter_id = chapter_id
        if chapter_id not in self.selected_chapter_ids:
            self.selected_chapter_ids = [chapter_id]
        self.notify_listeners()
