from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from .state_machine import ConversationState, ConversationStateMachine


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConversationSession:
    session_id: str = field(default_factory=lambda: f"conv_{uuid4().hex[:12]}")
    state_machine: ConversationStateMachine = field(default_factory=ConversationStateMachine)
    started_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def state(self) -> ConversationState:
        return self.state_machine.state

    def transition_to(self, target: ConversationState) -> ConversationState:
        return self.state_machine.transition_to(target)
