from __future__ import annotations

import json
from pathlib import Path

from runtime.conversation_archive import TranscriptRecord, TranscriptStore

from .authority import EvidenceAuthority
from .evidence_chunk import EvidenceChunk
from .evidence_source import EvidenceSourceType, EvidenceSpeaker


class ArchiveEvidenceChunker:
    """Split archive turns into separate Tony and Julia evidence chunks."""

    def __init__(self, store: TranscriptStore, *, project_root: str | Path | None = None):
        self.store = store
        root = Path(project_root) if project_root is not None else Path.cwd()
        self.quarantined_source_ids = self._load_quarantine(root / "data" / "memory_governance" / "quarantine.jsonl")

    def chunks(self) -> list[EvidenceChunk]:
        results: list[EvidenceChunk] = []
        for record in self.store.read_all():
            results.extend(self.from_record(record, quarantined_source_ids=self.quarantined_source_ids))
        return results

    @staticmethod
    def _load_quarantine(path: Path) -> set[str]:
        if not path.exists():
            return set()
        ids: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("status") == "quarantined" and item.get("source_id"):
                ids.add(str(item["source_id"]))
        return ids

    @staticmethod
    def from_record(record: TranscriptRecord, *, quarantined_source_ids: set[str] | None = None) -> list[EvidenceChunk]:
        chunks: list[EvidenceChunk] = []
        quarantined_source_ids = quarantined_source_ids or set()
        tony_id = f"archive:{record.session_id}:{record.turn_id}:tony"
        julia_id = f"archive:{record.session_id}:{record.turn_id}:julia"
        if record.user.strip() and tony_id not in quarantined_source_ids:
            chunks.append(EvidenceChunk(
                id=tony_id,
                source_type=EvidenceSourceType.ARCHIVE.value,
                content=record.user.strip(),
                session_id=record.session_id,
                turn_id=record.turn_id,
                timestamp=record.timestamp,
                speaker=EvidenceSpeaker.TONY.value,
                authority=EvidenceAuthority.for_source(EvidenceSourceType.ARCHIVE.value, speaker=EvidenceSpeaker.TONY.value),
                topics=list(record.topics or []),
                provenance={"origin": "tony_input", "verified": True, "archive_role": "experience_archive"},
            ))
        if record.assistant.strip() and julia_id not in quarantined_source_ids:
            chunks.append(EvidenceChunk(
                id=julia_id,
                source_type=EvidenceSourceType.ARCHIVE.value,
                content=record.assistant.strip(),
                session_id=record.session_id,
                turn_id=record.turn_id,
                timestamp=record.timestamp,
                speaker=EvidenceSpeaker.JULIA.value,
                authority=EvidenceAuthority.for_source(EvidenceSourceType.ARCHIVE.value, speaker=EvidenceSpeaker.JULIA.value),
                topics=list(record.topics or []),
                provenance={"origin": "assistant_response", "verified": False, "archive_role": "experience_archive"},
            ))
        return chunks
