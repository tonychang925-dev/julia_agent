from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParsedLLMResponse:
    text: str
    ok: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseParser:
    def parse_text(self, text: str, *, metadata: dict[str, Any] | None = None) -> ParsedLLMResponse:
        clean = text.strip()
        if not clean:
            return ParsedLLMResponse(text="", ok=False, error="empty response", metadata=metadata or {})
        return ParsedLLMResponse(text=clean, metadata=metadata or {})
