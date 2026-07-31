from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ContextBoundary:
    """Boundary used to reconstruct model-facing context after compaction."""

    boundary_id: str
    boundary_type: Literal["compact", "session_restore", "manual_checkpoint"]
    session_id: str
    summarized_record_ids: list[str] = field(default_factory=list)
    preserved_record_ids: list[str] = field(default_factory=list)
    compact_id: str | None = None
    created_at: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        boundary_type: Literal["compact", "session_restore", "manual_checkpoint"] = "compact",
        summarized_record_ids: list[str] | None = None,
        preserved_record_ids: list[str] | None = None,
        compact_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ContextBoundary":
        if not session_id:
            raise ValueError("session_id is required")
        return cls(
            boundary_id=f"ctx_boundary_{uuid4().hex}",
            boundary_type=boundary_type,
            session_id=session_id,
            summarized_record_ids=list(summarized_record_ids or []),
            preserved_record_ids=list(preserved_record_ids or []),
            compact_id=compact_id,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
