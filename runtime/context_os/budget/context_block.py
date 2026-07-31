from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Literal

from .token_estimator import estimate_tokens


BlockType = Literal[
    "core_identity",
    "relationship_anchor",
    "active_task",
    "session_state",
    "recent_turns",
    "semantic_evidence",
    "compact_state",
    "open_loops",
    "runtime_instruction",
    "known_failures",
    "emotional_context",
]


@dataclass(frozen=True)
class ContextBlock:
    block_id: str
    block_type: BlockType | str
    priority: int
    content: str
    required: bool = False
    estimated_tokens: int | None = None
    source_refs: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    authority_score: float = 0.0
    included: bool = True
    exclusion_reason: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.block_id:
            raise ValueError("block_id is required")
        if self.priority < 0:
            raise ValueError("priority must be >= 0")
        if self.authority_score < 0 or self.authority_score > 1:
            raise ValueError("authority_score must be in [0, 1]")
        if self.estimated_tokens is not None and self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be >= 0")

    @property
    def token_count(self) -> int:
        return self.estimated_tokens if self.estimated_tokens is not None else estimate_tokens(self.content)

    def include(self) -> "ContextBlock":
        return replace(self, included=True, exclusion_reason=None)

    def exclude(self, reason: str) -> "ContextBlock":
        return replace(self, included=False, exclusion_reason=reason)

    def clipped_to_tokens(self, max_tokens: int) -> "ContextBlock":
        if self.token_count <= max_tokens or max_tokens <= 0:
            return self
        approx_chars = max_tokens * 3
        clipped = self.content[:approx_chars].rstrip() + "…"
        return replace(self, content=clipped, estimated_tokens=max_tokens, metadata={**self.metadata, "clipped": True})

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["estimated_tokens"] = self.token_count
        return data
