from __future__ import annotations

from pathlib import Path

from runtime.conversation_archive import TranscriptStore
from runtime.memory import MemoryRuntime

from .archive_chunker import ArchiveEvidenceChunker
from .diary_chunker import DiaryEvidenceChunker
from .evidence_chunk import EvidenceChunk
from .memory_adapter import MemoryEvidenceAdapter


class CognitiveEvidenceStore:
    """Unified evidence source over diary, archive, and governed memory."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.diary_chunker = DiaryEvidenceChunker(self.project_root / "memory" / "claude_diary")
        self.archive_chunker = ArchiveEvidenceChunker(TranscriptStore.default(self.project_root), project_root=self.project_root)
        self.memory_adapter = MemoryEvidenceAdapter(MemoryRuntime(self.project_root))

    def load_all(self) -> list[EvidenceChunk]:
        return [
            *self.diary_chunker.chunks(),
            *self.archive_chunker.chunks(),
            *self.memory_adapter.chunks(),
        ]
