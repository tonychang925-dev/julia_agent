from __future__ import annotations

from dataclasses import dataclass, field

from .compact_schema import ExperienceCompactState


@dataclass
class InMemoryCompactStore:
    compacts: dict[str, ExperienceCompactState] = field(default_factory=dict)

    def save(self, compact: ExperienceCompactState) -> None:
        self.compacts[compact.compact_id] = compact

    def get(self, compact_id: str) -> ExperienceCompactState | None:
        return self.compacts.get(compact_id)

    def list_for_session(self, session_id: str) -> list[ExperienceCompactState]:
        return [c for c in self.compacts.values() if c.session_id == session_id]
