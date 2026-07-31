from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConflictItem:
    item_id: str
    claim: str
    source_type: str
    authority: float
    speaker: str | None = None
    provenance: str | None = None
    topic: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.item_id:
            raise ValueError("item_id is required")
        if not self.claim:
            raise ValueError("claim is required")
        if self.authority < 0 or self.authority > 1:
            raise ValueError("authority must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConflictResolution:
    conflict_id: str
    topic: str
    winner: ConflictItem | None
    rejected: list[ConflictItem] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.conflict_id:
            raise ValueError("conflict_id is required")
        if not self.topic:
            raise ValueError("topic is required")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("confidence must be in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["winner"] = self.winner.to_dict() if self.winner else None
        data["rejected"] = [item.to_dict() for item in self.rejected]
        return data
