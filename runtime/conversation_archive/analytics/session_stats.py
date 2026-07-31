from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from runtime.conversation_archive.transcript_record import TranscriptRecord


@dataclass(frozen=True)
class SessionStats:
    sessions: int
    turns_per_session: dict[str, int] = field(default_factory=dict)
    top_topics: list[tuple[str, int]] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "sessions": self.sessions,
            "turns_per_session": self.turns_per_session,
            "top_topics": self.top_topics,
            "open_loops": self.open_loops,
        }


class SessionStatsBuilder:
    def build(self, records: list[TranscriptRecord], *, top_n: int = 10) -> SessionStats:
        turns_by_session: dict[str, int] = defaultdict(int)
        topics: Counter[str] = Counter()
        open_loops: list[str] = []
        for record in records:
            turns_by_session[record.session_id] += 1
            for topic in record.topics:
                topics[topic] += 1
            for loop in record.open_loops:
                label = str(loop.get("topic") or loop.get("last_reference") or loop)
                if label and label not in open_loops:
                    open_loops.append(label)
        return SessionStats(
            sessions=len(turns_by_session),
            turns_per_session=dict(turns_by_session),
            top_topics=topics.most_common(top_n),
            open_loops=open_loops[:top_n],
        )
