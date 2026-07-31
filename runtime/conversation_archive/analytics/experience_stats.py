from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from runtime.conversation_archive.transcript_record import TranscriptRecord


@dataclass(frozen=True)
class ExperienceStats:
    total_turns: int
    experience_types: dict[str, int] = field(default_factory=dict)
    cognitive_modes: dict[str, int] = field(default_factory=dict)
    reflection_candidates: int = 0
    average_archive_priority: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_turns": self.total_turns,
            "experience_types": self.experience_types,
            "cognitive_modes": self.cognitive_modes,
            "reflection_candidates": self.reflection_candidates,
            "average_archive_priority": self.average_archive_priority,
        }


class ExperienceStatsBuilder:
    def build(self, records: list[TranscriptRecord]) -> ExperienceStats:
        type_counts: Counter[str] = Counter()
        mode_counts: Counter[str] = Counter()
        reflection_candidates = 0
        priority_sum = 0.0
        for record in records:
            metadata = record.experience_metadata or {}
            for item in metadata.get("experience_type", []) if isinstance(metadata, dict) else []:
                type_counts[str(item)] += 1
            if record.cognitive_mode:
                mode_counts[record.cognitive_mode] += 1
            if bool(metadata.get("reflection_candidate")):
                reflection_candidates += 1
            try:
                priority_sum += float(metadata.get("archive_priority", 0.0))
            except Exception:
                pass
        avg = round(priority_sum / len(records), 3) if records else 0.0
        return ExperienceStats(
            total_turns=len(records),
            experience_types=dict(type_counts),
            cognitive_modes=dict(mode_counts),
            reflection_candidates=reflection_candidates,
            average_archive_priority=avg,
        )
