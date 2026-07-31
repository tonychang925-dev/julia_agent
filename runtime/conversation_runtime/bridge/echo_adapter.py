from __future__ import annotations

from time import perf_counter
from collections.abc import Iterator

from tts.chunking import split_for_tts

from .cognitive_bridge import CognitiveBridge, CognitiveChunk, CognitiveResponse


class EchoAdapter(CognitiveBridge):
    """Local cognitive backend for Phase 3.2.1 state-machine validation."""

    def __init__(self, response_prefix: str = "你好 Tony"):
        self.response_prefix = response_prefix
        self._pending: dict[tuple[str, int], tuple[str, float]] = {}

    def send_message(self, text: str, *, session_id: str, turn_id: int) -> None:
        self._pending[(session_id, turn_id)] = (text, perf_counter())

    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        key = (session_id, turn_id)
        if key not in self._pending:
            return CognitiveResponse(
                text="",
                backend="echo_adapter",
                ok=False,
                error="no pending message for session/turn",
                metadata={"confidence": 0.0},
            )

        user_text, started = self._pending.pop(key)
        latency_ms = int((perf_counter() - started) * 1000)
        if "在吗" in user_text:
            text = "你好 Tony，我在。"
        else:
            text = self.response_prefix if not user_text else f"{self.response_prefix}，我听到了：{user_text}"
        return CognitiveResponse(
            text=text,
            backend="echo_adapter",
            metadata={
                "latency_ms": latency_ms,
                "model": "echo-v0",
                "token_usage": {"input_chars": len(user_text), "output_chars": len(text)},
                "confidence": 1.0,
            },
        )

    def stream_response(self, *, session_id: str, turn_id: int) -> Iterator[CognitiveChunk]:
        response = self.receive_response(session_id=session_id, turn_id=turn_id)
        chunks = split_for_tts(response.text, max_chars=12) or [response.text]
        for index, chunk in enumerate(chunks):
            yield CognitiveChunk(
                text=chunk,
                backend=response.backend,
                index=index,
                is_final=index == len(chunks) - 1,
                ok=response.ok,
                error=response.error,
                metadata={**response.metadata, "streaming": True, "chunk_count": len(chunks)},
            )
