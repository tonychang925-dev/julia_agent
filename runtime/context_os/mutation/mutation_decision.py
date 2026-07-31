from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .mutation_event import ContextMutationEvent


@dataclass(frozen=True)
class MutationDecision:
    event: ContextMutationEvent
    accepted: bool
    reason: str
    state_changes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "accepted": self.accepted,
            "reason": self.reason,
            "state_changes": asdict(self).get("state_changes", self.state_changes),
        }
