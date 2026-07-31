from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic, sleep
from collections.abc import Iterator
from typing import Any

from .cognitive_bridge import CognitiveBridge, CognitiveChunk, CognitiveResponse
from .handoff_protocol import (
    ClaudeHandoffRequest,
    ClaudeHandoffResponse,
    validate_response_payload,
)
from .response_reader import ResponseReader


@dataclass
class ClaudeCodeBridge(CognitiveBridge):
    """Phase 3.2.4.2 hardened file-handoff Claude Code bridge.

    No PTY/tmux/pexpect. The bridge writes both legacy text handoff and structured
    request JSON, then reads either structured response JSON or legacy text.
    """

    input_path: Path = Path("/tmp/julia_voice_input.txt")
    response_path: Path = Path("/tmp/julia_voice_response.txt")
    request_json_path: Path = Path("/tmp/julia_voice_request.json")
    response_json_path: Path = Path("/tmp/julia_voice_response.json")
    stream_jsonl_path: Path = Path("/tmp/julia_voice_response.stream.jsonl")
    timeout_s: float = 0.0
    poll_interval_s: float = 0.1
    response_reader: ResponseReader = field(default_factory=ResponseReader)
    _pending_started_at: dict[tuple[str, int], float] = field(default_factory=dict)

    @classmethod
    def from_paths(
        cls,
        input_path: str | Path = "/tmp/julia_voice_input.txt",
        response_path: str | Path = "/tmp/julia_voice_response.txt",
        *,
        request_json_path: str | Path = "/tmp/julia_voice_request.json",
        response_json_path: str | Path = "/tmp/julia_voice_response.json",
        stream_jsonl_path: str | Path = "/tmp/julia_voice_response.stream.jsonl",
        timeout_s: float = 0.0,
    ) -> "ClaudeCodeBridge":
        return cls(
            input_path=Path(input_path),
            response_path=Path(response_path),
            request_json_path=Path(request_json_path),
            response_json_path=Path(response_json_path),
            stream_jsonl_path=Path(stream_jsonl_path),
            timeout_s=timeout_s,
        )

    def send_message(self, text: str, *, session_id: str, turn_id: int) -> None:
        self.input_path.parent.mkdir(parents=True, exist_ok=True)
        self._clear_stale_outputs(session_id=session_id, turn_id=turn_id)
        self.input_path.write_text(text, encoding="utf-8")
        request = ClaudeHandoffRequest(
            session_id=session_id,
            turn_id=turn_id,
            text=text,
            correlation_id=f"{session_id}_turn_{turn_id:03d}",
        )
        request.write_json(self.request_json_path)
        self._pending_started_at[(session_id, turn_id)] = monotonic()

    def _clear_stale_outputs(self, *, session_id: str, turn_id: int) -> None:
        """Remove stale default handoff outputs before publishing a new request.

        Tests and a few local workflows pre-create a response file before calling
        send_message(); keep outputs that already belong to this exact turn.
        For the default /tmp legacy text response there is no turn metadata, so
        remove it aggressively to avoid reading a previous voice turn before the
        external watcher gets a chance to clean up.
        """
        for path in (self.response_json_path, self.stream_jsonl_path):
            if not path.exists():
                continue
            if self._output_matches_turn(path, session_id=session_id, turn_id=turn_id):
                continue
            try:
                path.unlink()
            except FileNotFoundError:
                pass

        if self.response_path == Path("/tmp/julia_voice_response.txt"):
            try:
                self.response_path.unlink()
            except FileNotFoundError:
                pass

    def _output_matches_turn(self, path: Path, *, session_id: str, turn_id: int) -> bool:
        try:
            if path.suffix == ".jsonl":
                first = next((line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()), "")
                if not first:
                    return False
                payload = json.loads(first)
            else:
                payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False
        return isinstance(payload, dict) and payload.get("session_id") == session_id and payload.get("turn_id") == turn_id

    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        key = (session_id, turn_id)
        started = self._pending_started_at.get(key, monotonic())

        available_path = self._wait_for_response_path()
        if available_path is None:
            return CognitiveResponse(
                text="",
                backend="claude_code",
                ok=False,
                error="timeout" if self.timeout_s > 0 else f"response file not found: {self.response_json_path} or {self.response_path}",
                metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="timeout" if self.timeout_s > 0 else "missing_response"),
            )

        if available_path == self.response_json_path:
            return self._read_structured_response(available_path, session_id=session_id, turn_id=turn_id, started=started)
        return self._read_legacy_response(available_path, started=started)

    def stream_response(self, *, session_id: str, turn_id: int) -> Iterator[CognitiveChunk]:
        """Read response chunks from JSONL when available; otherwise yield final response.

        JSONL line shape:
        {"type":"response_chunk","session_id":"...","turn_id":1,"text":"...","is_final":false}
        """
        key = (session_id, turn_id)
        started = self._pending_started_at.get(key, monotonic())

        if not self.stream_jsonl_path.exists():
            yield from super().stream_response(session_id=session_id, turn_id=turn_id)
            return

        emitted = 0
        try:
            lines = self.stream_jsonl_path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            yield CognitiveChunk(
                text="",
                backend="claude_code",
                index=0,
                is_final=True,
                ok=False,
                error=str(exc),
                metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="stream_read_failed"),
            )
            return

        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                yield CognitiveChunk(
                    text="",
                    backend="claude_code",
                    index=emitted,
                    is_final=True,
                    ok=False,
                    error=f"invalid stream json: {exc}",
                    metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="invalid_stream_json"),
                )
                return

            if payload.get("session_id") not in {None, session_id} or payload.get("turn_id") not in {None, turn_id}:
                yield CognitiveChunk(
                    text="",
                    backend="claude_code",
                    index=emitted,
                    is_final=True,
                    ok=False,
                    error="stream session_id/turn_id mismatch",
                    metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="stream_turn_mismatch"),
                )
                return

            text = str(payload.get("text", ""))
            is_final = bool(payload.get("is_final", False))
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            yield CognitiveChunk(
                text=text,
                backend="claude_code",
                index=emitted,
                is_final=is_final,
                ok=payload.get("status", "success") != "error",
                error=payload.get("reason"),
                metadata={
                    **self._metadata(started, model=str(metadata.get("model", "claude-code+deepseek")), confidence=1.0, status=str(payload.get("status", "success")), reason=payload.get("reason")),
                    **metadata,
                    "format": "stream_jsonl",
                },
            )
            emitted += 1

        if emitted == 0:
            yield CognitiveChunk(
                text="",
                backend="claude_code",
                index=0,
                is_final=True,
                ok=False,
                error="empty stream",
                metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="empty_stream"),
            )

    def _wait_for_response_path(self) -> Path | None:
        def existing() -> Path | None:
            if self.response_json_path.exists():
                return self.response_json_path
            if self.response_path.exists():
                return self.response_path
            return None

        found = existing()
        if found or self.timeout_s <= 0:
            return found

        deadline = monotonic() + self.timeout_s
        while monotonic() < deadline:
            found = existing()
            if found:
                return found
            sleep(self.poll_interval_s)
        return None

    def _read_structured_response(self, path: Path, *, session_id: str, turn_id: int, started: float) -> CognitiveResponse:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return self._error_response(started, f"invalid response json: {exc}", reason="invalid_json")

        if not isinstance(payload, dict):
            return self._error_response(started, "response json must be object", reason="invalid_schema")

        schema_errors = validate_response_payload(payload)
        if schema_errors:
            return self._error_response(started, "; ".join(schema_errors), reason="invalid_schema")

        response = ClaudeHandoffResponse.from_dict(payload)
        if response.session_id != session_id or response.turn_id != turn_id:
            return self._error_response(started, "response session_id/turn_id mismatch", reason="turn_mismatch")

        metadata = {
            **self._metadata(started, model=str(response.metadata.get("model", "claude-code+deepseek")), confidence=1.0 if response.status == "success" else 0.0, status=response.status, reason=response.reason),
            **response.metadata,
            "format": "handoff_json",
        }
        if response.status == "error":
            return CognitiveResponse(
                text=response.text,
                backend="claude_code",
                ok=False,
                error=response.reason or response.text or "claude_code_error",
                metadata=metadata,
            )
        if not response.text.strip():
            return CognitiveResponse(text="", backend="claude_code", ok=False, error="empty assistant response", metadata=metadata)
        return CognitiveResponse(text=response.text, backend="claude_code", metadata=metadata)

    def _read_legacy_response(self, path: Path, *, started: float) -> CognitiveResponse:
        try:
            envelope = self.response_reader.read_file(path)
        except Exception as exc:
            return self._error_response(started, str(exc), reason="read_failed")

        if not envelope.text.strip():
            return CognitiveResponse(
                text="",
                backend="claude_code",
                ok=False,
                error="empty assistant response",
                metadata={**self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason="empty_response"), **envelope.metadata},
            )

        return CognitiveResponse(
            text=envelope.text,
            backend="claude_code",
            metadata={**self._metadata(started, model="claude-code+deepseek", confidence=1.0, status="success", reason=None), **envelope.metadata},
        )

    def _error_response(self, started: float, error: str, *, reason: str) -> CognitiveResponse:
        return CognitiveResponse(
            text="",
            backend="claude_code",
            ok=False,
            error=error,
            metadata=self._metadata(started, model="claude-code+deepseek", confidence=0.0, status="error", reason=reason),
        )

    @staticmethod
    def _metadata(started: float, *, model: str, confidence: float, status: str, reason: str | None) -> dict[str, Any]:
        return {
            "latency_ms": int((monotonic() - started) * 1000),
            "model": model,
            "token_usage": None,
            "confidence": confidence,
            "handoff": "file",
            "status": status,
            "reason": reason,
        }
