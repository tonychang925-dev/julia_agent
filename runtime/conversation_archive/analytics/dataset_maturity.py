from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .archive_report import ArchiveAnalyticsReport


@dataclass(frozen=True)
class DatasetMaturityThresholds:
    min_turns: int = 1000
    min_sessions: int = 20
    min_modes: int = 4
    min_experience_types: int = 5


@dataclass(frozen=True)
class DatasetMaturityReport:
    ready_for_compression_design: bool
    thresholds: dict[str, int]
    observed: dict[str, int]
    gaps: list[str] = field(default_factory=list)
    recommendation: str = "collect_more_experience"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready_for_compression_design": self.ready_for_compression_design,
            "thresholds": self.thresholds,
            "observed": self.observed,
            "gaps": self.gaps,
            "recommendation": self.recommendation,
        }


class DatasetMaturityEvaluator:
    def __init__(self, thresholds: DatasetMaturityThresholds | None = None):
        self.thresholds = thresholds or DatasetMaturityThresholds()

    def evaluate(self, report: ArchiveAnalyticsReport) -> DatasetMaturityReport:
        observed = {
            "turns": int(report.total_turns),
            "sessions": int(report.sessions),
            "modes": len(report.cognitive_modes),
            "experience_types": len(report.experience_types),
        }
        thresholds = {
            "turns": self.thresholds.min_turns,
            "sessions": self.thresholds.min_sessions,
            "modes": self.thresholds.min_modes,
            "experience_types": self.thresholds.min_experience_types,
        }
        gaps: list[str] = []
        for key, required in thresholds.items():
            if observed[key] < required:
                gaps.append(f"{key}: observed {observed[key]} < required {required}")
        ready = not gaps
        return DatasetMaturityReport(
            ready_for_compression_design=ready,
            thresholds=thresholds,
            observed=observed,
            gaps=gaps,
            recommendation="ready_for_phase_3_6_9" if ready else "collect_more_experience_before_compact",
        )
