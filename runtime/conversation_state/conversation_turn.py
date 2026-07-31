from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_RUNTIME_METADATA_KEYS = {"provider", "backend", "model", "latency", "latency_ms", "tts", "stt", "session_id", "turn_id"}


@dataclass(frozen=True)
class ConversationTurn:
    """A completed conversation event as cognitive state, not runtime trace."""

    turn_id: int
    user_text: str
    assistant_text: str
    timestamp: str
    topics: list[str]
    cognitive_mode: str
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any], *, fallback_turn_id: int = 0) -> "ConversationTurn":
        metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        clean_metadata = {
            str(key): item
            for key, item in metadata.items()
            if str(key).lower() not in _RUNTIME_METADATA_KEYS
        }
        return cls(
            turn_id=int(value.get("turn_id", fallback_turn_id) or 0),
            user_text=str(value.get("user_text") or value.get("user") or ""),
            assistant_text=str(value.get("assistant_text") or value.get("assistant") or ""),
            timestamp=str(value.get("timestamp") or ""),
            topics=[str(item) for item in value.get("topics", [])] if isinstance(value.get("topics"), list) else [],
            cognitive_mode=str(value.get("cognitive_mode") or ""),
            metadata=clean_metadata,
        )

    def to_recent_dict(self) -> dict[str, str]:
        return {"user": self.user_text, "assistant": self.assistant_text}
