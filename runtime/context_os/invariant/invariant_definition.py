from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .invariant_type import InvariantType


class ProtectionLevel(str, Enum):
    WARNING = "warning"
    STRICT = "strict"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ContextInvariant:
    invariant_id: str
    invariant_type: InvariantType | str
    description: str
    protection_level: ProtectionLevel | str
    validation_rule: str
    protected_targets: list[str] = field(default_factory=list)
    allowed_sources: list[str] = field(default_factory=list)
    evidence_required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.invariant_id:
            raise ValueError("invariant_id is required")
        if not self.description:
            raise ValueError("description is required")
        object.__setattr__(self, "invariant_type", InvariantType(self.invariant_type))
        object.__setattr__(self, "protection_level", ProtectionLevel(self.protection_level))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["invariant_type"] = self.invariant_type.value
        data["protection_level"] = self.protection_level.value
        return data
