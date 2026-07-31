from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SessionSnapshot:
    """Traceable session resurrection seed.

    A snapshot is not raw memory. It records the compact state, preserved tail,
    and open-loop/task hints needed to rebuild Julia's model-facing world when a
    new session starts.
    """

    snapshot_id: str
    source_session_id: str
    compact_ids: list[str] = field(default_factory=list)
    preserved_record_ids: list[str] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    current_task: str = ""
    main_arc: str = ""
    relationship_context: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raise ValueError("snapshot_id is required")
        if not self.source_session_id:
            raise ValueError("source_session_id is required")

    @classmethod
    def create(
        cls,
        *,
        source_session_id: str,
        compact_ids: list[str] | None = None,
        preserved_record_ids: list[str] | None = None,
        open_loops: list[str] | None = None,
        next_actions: list[str] | None = None,
        current_task: str = "",
        main_arc: str = "",
        relationship_context: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SessionSnapshot":
        return cls(
            snapshot_id=f"ctx_snapshot_{uuid4().hex}",
            source_session_id=source_session_id,
            compact_ids=list(compact_ids or []),
            preserved_record_ids=list(preserved_record_ids or []),
            open_loops=list(open_loops or []),
            next_actions=list(next_actions or []),
            current_task=current_task,
            main_arc=main_arc,
            relationship_context=list(relationship_context or []),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
