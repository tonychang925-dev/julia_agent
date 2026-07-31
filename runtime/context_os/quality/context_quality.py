from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ContextQuality:
    plan_id: str
    identity_coverage: float
    relationship_coverage: float
    task_coverage: float
    evidence_confidence: float
    budget_utilization: float
    hallucination_risk: float
    highest_authority: float
    evidence_count: int
    low_authority_evidence_count: int
    assistant_generated_ratio: float
    conflict_count: int = 0
    pass_gate: bool = True
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for field_name in [
            "identity_coverage",
            "relationship_coverage",
            "task_coverage",
            "evidence_confidence",
            "budget_utilization",
            "hallucination_risk",
            "highest_authority",
            "assistant_generated_ratio",
        ]:
            value = getattr(self, field_name)
            if value < 0 or value > 1:
                raise ValueError(f"{field_name} must be in [0, 1]")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be >= 0")
        if self.low_authority_evidence_count < 0:
            raise ValueError("low_authority_evidence_count must be >= 0")
        if self.conflict_count < 0:
            raise ValueError("conflict_count must be >= 0")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
