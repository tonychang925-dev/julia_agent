from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .archive_report import ArchiveAnalyticsReport


DEFAULT_MODE_TARGET_DISTRIBUTION: dict[str, float] = {
    "engineering_collaboration": 0.40,
    "emotional_support": 0.20,
    "learning_mode": 0.20,
    "private_voice_continuity": 0.10,
    "planning_debugging": 0.10,
}

DEFAULT_EXPERIENCE_TYPE_MINIMUMS: dict[str, int] = {
    "technical": 100,
    "decision": 50,
    "milestone": 30,
    "relationship": 80,
    "emotion": 50,
    "casual": 30,
}


@dataclass(frozen=True)
class CollectionPlanItem:
    dimension: str
    name: str
    observed: int
    target: int
    gap: int
    priority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "name": self.name,
            "observed": self.observed,
            "target": self.target,
            "gap": self.gap,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class ExperienceCollectionPlan:
    target_turns: int
    observed_turns: int
    remaining_turns: int
    items: list[CollectionPlanItem] = field(default_factory=list)
    recommended_focus: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_turns": self.target_turns,
            "observed_turns": self.observed_turns,
            "remaining_turns": self.remaining_turns,
            "items": [item.to_dict() for item in self.items],
            "recommended_focus": self.recommended_focus,
        }


class ExperienceCollectionPlanner:
    """Planner for collecting a balanced Experience Corpus before compaction."""

    def __init__(
        self,
        *,
        target_turns: int = 1000,
        mode_distribution: dict[str, float] | None = None,
        experience_type_minimums: dict[str, int] | None = None,
    ):
        self.target_turns = target_turns
        self.mode_distribution = mode_distribution or DEFAULT_MODE_TARGET_DISTRIBUTION
        self.experience_type_minimums = experience_type_minimums or DEFAULT_EXPERIENCE_TYPE_MINIMUMS

    def build(self, report: ArchiveAnalyticsReport) -> ExperienceCollectionPlan:
        items: list[CollectionPlanItem] = []
        for mode, ratio in self.mode_distribution.items():
            target = int(round(self.target_turns * ratio))
            observed = int(report.cognitive_modes.get(mode, 0))
            gap = max(0, target - observed)
            if gap:
                items.append(CollectionPlanItem("cognitive_mode", mode, observed, target, gap, self._priority(gap, target)))
        for exp_type, target in self.experience_type_minimums.items():
            observed = int(report.experience_types.get(exp_type, 0))
            gap = max(0, target - observed)
            if gap:
                items.append(CollectionPlanItem("experience_type", exp_type, observed, target, gap, self._priority(gap, target)))
        items = sorted(items, key=lambda item: (self._priority_rank(item.priority), item.gap), reverse=True)
        focus = [f"{item.dimension}:{item.name}" for item in items[:5]]
        return ExperienceCollectionPlan(
            target_turns=self.target_turns,
            observed_turns=report.total_turns,
            remaining_turns=max(0, self.target_turns - report.total_turns),
            items=items,
            recommended_focus=focus,
        )

    @staticmethod
    def _priority(gap: int, target: int) -> str:
        if target <= 0:
            return "low"
        ratio = gap / target
        if ratio >= 0.75:
            return "high"
        if ratio >= 0.35:
            return "medium"
        return "low"

    @staticmethod
    def _priority_rank(priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)
