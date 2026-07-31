from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from runtime.context_os.compact import ExperienceCompactState

from .projection_block import ContextProjectionBlock


@dataclass
class CompactProjection:
    def project(self, compacts: Iterable[ExperienceCompactState] = ()) -> list[ContextProjectionBlock]:
        blocks: list[ContextProjectionBlock] = []
        for compact in compacts:
            blocks.append(ContextProjectionBlock(
                block_id=f"projection_compact_{compact.compact_id}",
                block_type="compact_state",
                source_refs=[compact.compact_id, *compact.source_record_ids],
                evidence_ids=list(compact.source_evidence_ids),
                content=compact.to_context_block_text(),
                priority=88,
                authority=compact.confidence,
                required=False,
                metadata={"projection": "compact", "compact_id": compact.compact_id},
            ))
        return blocks
