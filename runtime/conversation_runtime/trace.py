from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tts.interface import TTSResult

from .turn_manager import ConversationTurn
from .state_machine import ConversationState


@dataclass(frozen=True)
class ConversationTrace:
    session_id: str
    turn_id: int
    input: dict[str, Any]
    reasoning: dict[str, Any]
    response: dict[str, Any]
    audio: dict[str, Any]
    state_trace: list[str]
    latency: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_turn(
        cls,
        turn: ConversationTurn,
        *,
        state_history: list[ConversationState],
        tts_result: TTSResult | None = None,
        latency: dict[str, object] | None = None,
    ) -> "ConversationTrace":
        return cls(
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            input={"text": turn.user.text},
            reasoning={
                "backend": turn.assistant.cognitive_backend,
                "metadata": turn.assistant.metadata,
            },
            response={"text": turn.assistant.text},
            audio={
                "tts": tts_result.engine if tts_result else None,
                "ok": tts_result.ok if tts_result else None,
                "duration_ms": tts_result.duration_ms if tts_result else None,
            },
            state_trace=[state.name for state in state_history if state is not ConversationState.IDLE],
            latency=latency or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "input": self.input,
            "reasoning": self.reasoning,
            "response": self.response,
            "audio": self.audio,
            "state_trace": self.state_trace,
            "latency": self.latency,
        }
