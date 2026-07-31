from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RelationshipStore:
    """Read-only relationship state store for Phase 3.5.2.

    Phase 3.5.2 intentionally avoids memory/reflection writes. If the optional
    relationship state file is missing, a stable default state is returned.
    """

    DEFAULT_STATE: dict[str, Any] = {
        "relationship_stage": "long_term_collaboration",
        "shared_projects": ["Julia Runtime", "AI Agent Architecture"],
        "interaction_preferences": ["warm", "concise", "technical_when_needed", "natural", "context_continuity"],
        "current_mode": "engineering_collaboration",
    }

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.path = self.project_root / "relationship" / "relationship_state.json"

    def load_state(self) -> dict[str, Any]:
        state = dict(self.DEFAULT_STATE)
        if not self.path.exists():
            return state
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return state
        if not isinstance(loaded, dict):
            return state
        for key in ["relationship_stage", "shared_projects", "interaction_preferences", "current_mode"]:
            if key in loaded:
                state[key] = loaded[key]
        return state
