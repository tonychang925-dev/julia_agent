from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path

from .transcript_record import TranscriptRecord


@dataclass
class TranscriptStore:
    path: Path

    @classmethod
    def default(cls, project_root: Path | None = None) -> "TranscriptStore":
        root = project_root or Path(__file__).resolve().parents[2]
        return cls(root / "data" / "conversation_archive" / "transcripts.jsonl")

    def append(self, record: TranscriptRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    def append_trace(self, trace: object) -> TranscriptRecord:
        record = TranscriptRecord.from_trace(trace)
        self.append(record)
        return record

    def read_all(self) -> list[TranscriptRecord]:
        if not self.path.exists():
            return []
        records: list[TranscriptRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            records.append(self._record_from_dict(data))
        return records

    def tail(self, limit: int = 10) -> list[TranscriptRecord]:
        records = self.read_all()
        return records[-max(0, limit):]

    @staticmethod
    def _record_from_dict(data: dict) -> TranscriptRecord:
        allowed = {field.name for field in fields(TranscriptRecord)}
        cleaned = {key: value for key, value in data.items() if key in allowed}
        cleaned.setdefault("experience_metadata", {})
        return TranscriptRecord(**cleaned)
