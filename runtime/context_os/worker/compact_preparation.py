from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.proposal import ProposalType, StateProposal

from .worker_event import WorkerEvent


@dataclass
class CompactPreparationWorker:
    min_turns_for_compact: int = 100

    def analyze(self, event: WorkerEvent) -> list[StateProposal]:
        turn_count = int(event.payload.get("turn_count") or 0)
        if event.event_type != "turn_completed" or turn_count < self.min_turns_for_compact:
            return []
        return [
            StateProposal.create(
                ProposalType.COMPACT_CANDIDATE,
                source_turn_id=event.source_turn_id,
                summary="Conversation window is eligible for structured compact preparation.",
                target="compact",
                payload={"turn_count": turn_count, "level": "medium"},
                confidence=0.68,
                evidence_refs=[event.source_turn_id],
                metadata={"worker": "compact_preparation"},
            )
        ]
