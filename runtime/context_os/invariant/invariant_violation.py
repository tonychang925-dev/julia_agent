from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ViolationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class InvariantViolation:
    invariant_id: str
    source: str
    attempted_change: str
    severity: ViolationSeverity | str
    reason: str
    violation_id: str = field(default_factory=lambda: f"invariant_violation_{uuid4().hex}")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.invariant_id:
            raise ValueError("invariant_id is required")
        if not self.source:
            raise ValueError("source is required")
        if not self.reason:
            raise ValueError("reason is required")
        object.__setattr__(self, "severity", ViolationSeverity(self.severity))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data
