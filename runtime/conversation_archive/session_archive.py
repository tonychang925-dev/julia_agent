from __future__ import annotations

from dataclasses import dataclass

from .transcript_record import TranscriptRecord


@dataclass(frozen=True)
class SessionArchiveSummary:
    session_id: str
    turn_count: int
    topics: list[str]
    last_user: str
    last_assistant: str


class SessionArchive:
    """Small helper for grouping transcript records by session."""

    @staticmethod
    def summarize(records: list[TranscriptRecord]) -> SessionArchiveSummary | None:
        if not records:
            return None
        topics: list[str] = []
        for record in records:
            for topic in record.topics:
                if topic not in topics:
                    topics.append(topic)
        last = records[-1]
        return SessionArchiveSummary(
            session_id=last.session_id,
            turn_count=len(records),
            topics=topics,
            last_user=last.user,
            last_assistant=last.assistant,
        )
