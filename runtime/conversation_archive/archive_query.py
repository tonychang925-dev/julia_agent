from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .transcript_record import TranscriptRecord
from .transcript_store import TranscriptStore


@dataclass(frozen=True)
class ArchiveQuery:
    text_contains: str | None = None
    session_id: str | None = None
    experience_type: str | None = None
    reflection_candidate: bool | None = None
    min_archive_priority: float | None = None
    limit: int = 20


@dataclass(frozen=True)
class ArchiveQueryResult:
    records: list[TranscriptRecord] = field(default_factory=list)
    total_scanned: int = 0

    @property
    def count(self) -> int:
        return len(self.records)


class ArchiveQueryEngine:
    """Small typed query layer over the experience archive.

    This is deliberately lexical/filter-based for 3.6.8.1. Semantic retrieval
    belongs to Phase 3.6.10 and should build on this API rather than reading
    JSONL directly.
    """

    def __init__(self, store: TranscriptStore):
        self.store = store

    def query(self, query: ArchiveQuery) -> ArchiveQueryResult:
        records = self.store.read_all()
        matched = [record for record in records if self._matches(record, query)]
        limit = max(0, query.limit)
        if limit:
            matched = matched[-limit:]
        return ArchiveQueryResult(records=matched, total_scanned=len(records))

    def latest_reflection_candidates(self, limit: int = 20) -> ArchiveQueryResult:
        return self.query(ArchiveQuery(reflection_candidate=True, limit=limit))

    @staticmethod
    def _matches(record: TranscriptRecord, query: ArchiveQuery) -> bool:
        if query.session_id and record.session_id != query.session_id:
            return False
        if query.text_contains:
            needle = query.text_contains.lower()
            if needle not in f"{record.user}\n{record.assistant}".lower():
                return False
        metadata = record.experience_metadata or {}
        types = metadata.get("experience_type") if isinstance(metadata, dict) else []
        if query.experience_type and query.experience_type not in types:
            return False
        if query.reflection_candidate is not None and bool(metadata.get("reflection_candidate")) != query.reflection_candidate:
            return False
        if query.min_archive_priority is not None:
            try:
                priority = float(metadata.get("archive_priority", 0.0))
            except Exception:
                priority = 0.0
            if priority < query.min_archive_priority:
                return False
        return True
