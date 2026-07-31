from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitiveResponse:
    text: str
    backend: str
    ok: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveChunk:
    text: str
    backend: str
    index: int
    is_final: bool = False
    ok: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CognitiveBridge(ABC):
    @abstractmethod
    def send_message(self, text: str, *, session_id: str, turn_id: int) -> None:
        ...

    @abstractmethod
    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        ...

    def stream_response(self, *, session_id: str, turn_id: int) -> Iterator[CognitiveChunk]:
        """Phase 3.2.5 streaming hook.

        Non-streaming bridges yield one final chunk derived from receive_response.
        """
        response = self.receive_response(session_id=session_id, turn_id=turn_id)
        yield CognitiveChunk(
            text=response.text,
            backend=response.backend,
            index=0,
            is_final=True,
            ok=response.ok,
            error=response.error,
            metadata=response.metadata,
        )
