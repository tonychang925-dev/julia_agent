from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssistantResponseEnvelope:
    type: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseReader:
    """Normalizes raw backend output into assistant_response envelopes."""

    def read_text(self, raw: str) -> AssistantResponseEnvelope:
        raw = raw.strip()
        if not raw:
            return AssistantResponseEnvelope(type="assistant_response", text="", metadata={"empty": True})

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return AssistantResponseEnvelope(type="assistant_response", text=raw, metadata={"format": "plain_text"})

        if isinstance(payload, dict):
            text = str(payload.get("text") or payload.get("response") or payload.get("content") or "")
            envelope_type = str(payload.get("type") or "assistant_response")
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            metadata = {**metadata, "format": "json"}
            return AssistantResponseEnvelope(type=envelope_type, text=text, metadata=metadata)

        return AssistantResponseEnvelope(type="assistant_response", text=str(payload), metadata={"format": "json_scalar"})

    def read_file(self, path: str | Path) -> AssistantResponseEnvelope:
        return self.read_text(Path(path).read_text(encoding="utf-8"))
