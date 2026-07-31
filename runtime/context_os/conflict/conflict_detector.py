from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from runtime.context_os.budget import ContextBlock

from .resolution import ConflictItem


@dataclass
class ConflictDetector:
    def items_from_blocks(self, blocks: Iterable[ContextBlock]) -> list[ConflictItem]:
        items: list[ConflictItem] = []
        for block in blocks:
            topic = str(block.metadata.get("conflict_topic") or block.metadata.get("topic") or block.block_type)
            provenance = str(block.metadata.get("provenance") or block.metadata.get("origin") or "") or None
            speaker = str(block.metadata.get("speaker") or "") or None
            items.append(ConflictItem(
                item_id=block.block_id,
                claim=block.content,
                source_type=str(block.block_type),
                authority=block.authority_score,
                speaker=speaker,
                provenance=provenance,
                topic=topic,
                metadata={"source_refs": block.source_refs, "evidence_ids": block.evidence_ids, **block.metadata},
            ))
        return items

    def group_conflicts(self, items: Iterable[ConflictItem]) -> dict[str, list[ConflictItem]]:
        groups: dict[str, list[ConflictItem]] = {}
        for item in items:
            topic = item.topic or "general"
            groups.setdefault(topic, []).append(item)
        return {topic: vals for topic, vals in groups.items() if len(vals) > 1}
