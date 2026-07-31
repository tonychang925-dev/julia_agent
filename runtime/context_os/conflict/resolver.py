from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import uuid4

from runtime.context_os.budget import ContextBlock

from .conflict_detector import ConflictDetector
from .conflict_policy import ConflictPolicy
from .resolution import ConflictItem, ConflictResolution


@dataclass
class ContextConflictResolver:
    detector: ConflictDetector = field(default_factory=ConflictDetector)
    policy: ConflictPolicy = field(default_factory=ConflictPolicy)

    def resolve_items(self, items: list[ConflictItem]) -> list[ConflictResolution]:
        resolutions: list[ConflictResolution] = []
        for topic, group in self.detector.group_conflicts(items).items():
            ordered = sorted(group, key=self.policy.priority, reverse=True)
            winner = ordered[0]
            rejected = ordered[1:]
            confidence_gap = self.policy.priority(winner) - self.policy.priority(rejected[0]) if rejected else self.policy.priority(winner)
            resolutions.append(ConflictResolution(
                conflict_id=f"ctx_conflict_{uuid4().hex}",
                topic=topic,
                winner=winner,
                rejected=rejected,
                reason=f"winner_selected_by_authority_policy:{winner.item_id}",
                confidence=max(0.0, min(1.0, 0.55 + confidence_gap / 2)),
            ))
        return resolutions

    def resolve_blocks(self, blocks: list[ContextBlock]) -> tuple[list[ContextBlock], list[ConflictResolution]]:
        items = self.detector.items_from_blocks(blocks)
        resolutions = self.resolve_items(items)
        rejected_ids = {item.item_id for res in resolutions for item in res.rejected}
        winner_ids = {res.winner.item_id for res in resolutions if res.winner}
        resolved: list[ContextBlock] = []
        for block in blocks:
            if block.block_id in rejected_ids:
                resolved.append(block.exclude("rejected_by_context_conflict_resolver"))
            elif block.block_id in winner_ids:
                resolved.append(replace(block, metadata={**block.metadata, "conflict_winner": True}).include())
            else:
                resolved.append(block)
        return resolved, resolutions
