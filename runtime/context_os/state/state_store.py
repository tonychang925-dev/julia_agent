from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .session_state import JuliaSessionState
from .task_state import JuliaTaskState


@dataclass
class ContextStateStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        (self.root / "sessions").mkdir(parents=True, exist_ok=True)
        (self.root / "tasks").mkdir(parents=True, exist_ok=True)

    def session_path(self, session_id: str) -> Path:
        return self.root / "sessions" / f"{session_id}.json"

    def task_path(self, task_id: str) -> Path:
        return self.root / "tasks" / f"{task_id}.json"

    def save_session(self, state: JuliaSessionState) -> Path:
        path = self.session_path(state.session_id)
        path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_session(self, session_id: str) -> JuliaSessionState | None:
        path = self.session_path(session_id)
        if not path.exists():
            return None
        return JuliaSessionState.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save_task(self, state: JuliaTaskState) -> Path:
        path = self.task_path(state.task_id)
        path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_task(self, task_id: str) -> JuliaTaskState | None:
        path = self.task_path(task_id)
        if not path.exists():
            return None
        return JuliaTaskState.from_dict(json.loads(path.read_text(encoding="utf-8")))
