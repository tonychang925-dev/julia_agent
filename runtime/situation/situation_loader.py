from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SituationLoader:
    """Loads explicit current situation state with stable defaults."""

    DEFAULT_STATE: dict[str, Any] = {
        "current_activity": "building Julia Cognitive Environment",
        "environment": "software_architecture",
        "goal": "reconstruct Claude implicit cognitive environment inside Julia Runtime",
        "interaction_mode": "engineering_collaboration",
        "active_topics": ["Julia Runtime", "Phase 3.5", "cognitive architecture", "memory architecture"],
    }

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.path = self.project_root / "situation" / "situation_state.json"

    def load(self) -> dict[str, Any]:
        state = dict(self.DEFAULT_STATE)
        state["active_topics"] = list(self.DEFAULT_STATE["active_topics"])
        if not self.path.exists():
            return state
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return state
        if not isinstance(loaded, dict):
            return state
        for key in ["current_activity", "environment", "goal", "interaction_mode", "active_topics"]:
            if key in loaded:
                state[key] = loaded[key]
        return state
