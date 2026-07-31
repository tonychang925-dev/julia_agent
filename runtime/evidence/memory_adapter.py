from __future__ import annotations

from runtime.memory import MemoryObject, MemoryRuntime

from .authority import EvidenceAuthority
from .evidence_chunk import EvidenceChunk
from .evidence_source import EvidenceSourceType, EvidenceSpeaker


class MemoryEvidenceAdapter:
    def __init__(self, memory_runtime: MemoryRuntime):
        self.memory_runtime = memory_runtime

    def chunks(self) -> list[EvidenceChunk]:
        return [self.from_memory(memory) for memory in self.memory_runtime.store.load_all()]

    @staticmethod
    def from_memory(memory: MemoryObject) -> EvidenceChunk:
        return EvidenceChunk(
            id=f"memory:{memory.id}",
            source_type=EvidenceSourceType.MEMORY.value,
            content=memory.summary,
            speaker=EvidenceSpeaker.MEMORY.value,
            authority=EvidenceAuthority.for_source(EvidenceSourceType.MEMORY.value, governed=True),
            topics=list(memory.topics or []),
            provenance={
                "origin": "governed_memory",
                "verified": True,
                "memory_id": memory.id,
                "memory_type": memory.type,
                "importance": memory.importance,
            },
        )
