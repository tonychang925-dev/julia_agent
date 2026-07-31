from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ResurrectionRequest:
    """Cold-start request describing which Julia cognitive state to restore."""

    user_id: str
    session_id: str | None = None
    target_time: str | None = None
    task_hint: str | None = None
    request_id: str = field(default_factory=lambda: f"resurrection_request_{uuid4().hex}")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
