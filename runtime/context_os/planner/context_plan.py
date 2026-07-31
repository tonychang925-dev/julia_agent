from __future__ import annotations

from dataclasses import asdict, dataclass, field
from uuid import uuid4

from .context_intent import ContextIntentType
from .evidence_intent import EvidenceIntentType


@dataclass(frozen=True)
class ContextPlan:
    """Planner output describing what cognitive world this turn requires.

    It intentionally carries semantic evidence intents rather than concrete
    keywords or file paths. Retrieval remains a downstream Context OS tool.
    """

    query: str
    cognitive_mode: str
    intent_type: ContextIntentType
    required_blocks: list[str] = field(default_factory=list)
    optional_blocks: list[str] = field(default_factory=list)
    evidence_intents: list[EvidenceIntentType] = field(default_factory=list)
    excluded_blocks: list[str] = field(default_factory=list)
    target_budget_tokens: int = 12000
    reason: str = ""
    planner_confidence: float = 0.0
    plan_id: str = field(default_factory=lambda: f"ctx_plan_{uuid4().hex}")

    def __post_init__(self) -> None:
        if not self.query:
            raise ValueError("query is required")
        if self.target_budget_tokens <= 0:
            raise ValueError("target_budget_tokens must be positive")
        if self.planner_confidence < 0 or self.planner_confidence > 1:
            raise ValueError("planner_confidence must be in [0, 1]")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["intent_type"] = self.intent_type.value
        data["evidence_intents"] = [intent.value for intent in self.evidence_intents]
        return data
