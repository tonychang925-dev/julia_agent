from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .runtime_event import RuntimeEvent


@dataclass
class RuntimeEventStore:
    path: Path

    @classmethod
    def default(cls, project_root: Path | None = None) -> "RuntimeEventStore":
        root = project_root or Path(__file__).resolve().parents[2]
        return cls(root / "data" / "runtime_trace" / "runtime_events.jsonl")

    def append(self, event: RuntimeEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def append_trace(self, trace: object) -> RuntimeEvent:
        event = RuntimeEvent.from_trace(trace)
        self.append(event)
        return event
