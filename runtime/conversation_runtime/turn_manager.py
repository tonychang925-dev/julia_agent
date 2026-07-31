from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .session import utc_now_iso


@dataclass
class UserTurn:
    turn_id: int
    text: str = ""
    speech_segment: Any | None = None
    started_at: str = field(default_factory=utc_now_iso)
    finalized_at: str | None = None


@dataclass
class AssistantTurn:
    turn_id: int
    text: str = ""
    cognitive_backend: str = ""
    tts_result: Any | None = None
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    session_id: str
    turn_id: int
    user: UserTurn
    assistant: AssistantTurn
    correlation_id: str


class TurnManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._next_turn_id = 1
        self.turns: list[ConversationTurn] = []

    def start_turn(self, user_text: str = "") -> ConversationTurn:
        turn_id = self._next_turn_id
        self._next_turn_id += 1
        turn = ConversationTurn(
            session_id=self.session_id,
            turn_id=turn_id,
            user=UserTurn(turn_id=turn_id, text=user_text),
            assistant=AssistantTurn(turn_id=turn_id),
            correlation_id=f"{self.session_id}_turn_{turn_id:03d}",
        )
        self.turns.append(turn)
        return turn

    def finalize_user_text(self, turn: ConversationTurn, text: str) -> None:
        turn.user.text = text
        turn.user.finalized_at = utc_now_iso()

    def complete_assistant(
        self,
        turn: ConversationTurn,
        *,
        text: str,
        backend: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        turn.assistant.text = text
        turn.assistant.cognitive_backend = backend
        turn.assistant.metadata = metadata or {}
        turn.assistant.completed_at = utc_now_iso()
