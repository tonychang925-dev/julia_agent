from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    source_type: str
    content: str
    source_path: str | None = None
    session_id: str | None = None
    turn_id: int | None = None
    timestamp: str | None = None
    speaker: str | None = None
    authority: float = 0.0
    topics: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_prompt_block(self) -> str:
        location = self.source_path or self.session_id or self.id
        if self.turn_id is not None:
            location = f"{location}:turn-{self.turn_id}"
        speaker = f" speaker={self.speaker}" if self.speaker else ""
        return f"[{self.source_type}:{location} authority={self.authority:.2f}{speaker}]\n{self.content.strip()}"
