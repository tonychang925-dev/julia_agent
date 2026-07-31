from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from runtime.memory import MemoryObject
from runtime.memory.memory_object import make_memory_id, normalize_importance, normalize_memory_type


@dataclass(frozen=True)
class MemoryCandidate:
    """Reflection output before Memory Runtime persistence."""

    memory_type: str
    summary: str
    reason: str
    importance: dict[str, float]
    confidence: float
    topics: list[str]
    source: str

    def total_importance(self) -> float:
        values = [float(self.importance.get(key, 0.0) or 0.0) for key in ("emotional", "relationship", "technical", "recurrence")]
        return sum(values) / len(values)

    def to_memory_object(self, *, index: int = 1, timestamp: str | None = None) -> MemoryObject:
        memory_type = normalize_memory_type(self.memory_type)
        summary = self.summary.strip()
        return MemoryObject(
            id=make_memory_id(memory_type=memory_type, source=self.source, title=summary[:48], index=index),
            type=memory_type,
            summary=summary,
            content={"reason": self.reason, "confidence": self.confidence},
            topics=list(self.topics),
            importance=normalize_importance(self.importance, memory_type=memory_type),
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            source=self.source,
        )
