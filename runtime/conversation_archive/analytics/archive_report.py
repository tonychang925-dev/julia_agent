from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.conversation_archive.transcript_store import TranscriptStore

from .experience_stats import ExperienceStatsBuilder
from .session_stats import SessionStatsBuilder


@dataclass(frozen=True)
class ArchiveAnalyticsReport:
    generated_at: str
    archive_path: str
    total_turns: int
    sessions: int
    experience_types: dict[str, int]
    cognitive_modes: dict[str, int]
    top_topics: list[tuple[str, int]]
    open_loops: list[str]
    reflection_candidates: int
    average_archive_priority: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "archive_path": self.archive_path,
            "total_turns": self.total_turns,
            "sessions": self.sessions,
            "experience_types": self.experience_types,
            "cognitive_modes": self.cognitive_modes,
            "top_topics": self.top_topics,
            "open_loops": self.open_loops,
            "reflection_candidates": self.reflection_candidates,
            "average_archive_priority": self.average_archive_priority,
        }


class ArchiveAnalyticsReporter:
    def __init__(self, store: TranscriptStore):
        self.store = store

    @classmethod
    def default(cls, project_root: Path | None = None) -> "ArchiveAnalyticsReporter":
        return cls(TranscriptStore.default(project_root))

    def build(self) -> ArchiveAnalyticsReport:
        records = self.store.read_all()
        exp = ExperienceStatsBuilder().build(records)
        ses = SessionStatsBuilder().build(records)
        return ArchiveAnalyticsReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            archive_path=str(self.store.path),
            total_turns=exp.total_turns,
            sessions=ses.sessions,
            experience_types=exp.experience_types,
            cognitive_modes=exp.cognitive_modes,
            top_topics=ses.top_topics,
            open_loops=ses.open_loops,
            reflection_candidates=exp.reflection_candidates,
            average_archive_priority=exp.average_archive_priority,
        )
