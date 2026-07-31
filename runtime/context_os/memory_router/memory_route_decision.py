from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MemoryRouteDecision:
    memory_id: str
    action: str  # inject / suppress / defer
    scope: str  # engineering / emotional / relationship / learning / planning
    reason: str
    provenance_required: bool
    confidence: float
    memory_class: str | None = None
    allowed_domains: tuple[str, ...] = field(default_factory=tuple)
    blocked_domains: tuple[str, ...] = field(default_factory=tuple)
    provenance_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["allowed_domains"] = list(self.allowed_domains)
        data["blocked_domains"] = list(self.blocked_domains)
        return data
