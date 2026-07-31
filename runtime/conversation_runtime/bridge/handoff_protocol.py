from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..session import utc_now_iso


@dataclass(frozen=True)
class ClaudeHandoffRequest:
    session_id: str
    turn_id: int
    text: str
    timestamp: str = field(default_factory=utc_now_iso)
    backend: str = "claude_code"
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}

    def write_json(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass(frozen=True)
class ClaudeHandoffResponse:
    session_id: str
    turn_id: int
    status: str
    text: str
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ClaudeHandoffResponse":
        return cls(
            session_id=str(payload.get("session_id", "")),
            turn_id=int(payload.get("turn_id", 0)),
            status=str(payload.get("status", "error")),
            text=str(payload.get("text", "")),
            reason=str(payload["reason"]) if payload.get("reason") is not None else None,
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )


def validate_request_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["session_id", "turn_id", "timestamp", "text", "backend"]:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("backend") != "claude_code":
        errors.append("backend must be claude_code")
    if "turn_id" in payload and (not isinstance(payload["turn_id"], int) or payload["turn_id"] < 1):
        errors.append("turn_id must be integer >= 1")
    return errors


def validate_response_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["session_id", "turn_id", "status", "text"]:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("status") not in {"success", "error"}:
        errors.append("status must be success or error")
    if "turn_id" in payload and (not isinstance(payload["turn_id"], int) or payload["turn_id"] < 1):
        errors.append("turn_id must be integer >= 1")
    return errors
