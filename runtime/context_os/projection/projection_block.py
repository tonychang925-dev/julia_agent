from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from runtime.context_os.budget import ContextBlock


@dataclass(frozen=True)
class ContextProjectionBlock:
    block_id: str
    block_type: str
    source_refs: list[str]
    content: str
    priority: int
    estimated_tokens: int | None = None
    authority: float = 0.0
    required: bool = False
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.block_id:
            raise ValueError("block_id is required")
        if not self.block_type:
            raise ValueError("block_type is required")
        if self.authority < 0 or self.authority > 1:
            raise ValueError("authority must be in [0, 1]")
        if self.priority < 0:
            raise ValueError("priority must be >= 0")

    def to_context_block(self) -> ContextBlock:
        return ContextBlock(
            block_id=self.block_id,
            block_type=self.block_type,
            priority=self.priority,
            content=self.content,
            required=self.required,
            estimated_tokens=self.estimated_tokens,
            source_refs=list(self.source_refs),
            evidence_ids=list(self.evidence_ids),
            authority_score=self.authority,
            metadata={**self.metadata, "projection_block": True},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
