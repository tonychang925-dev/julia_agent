from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.proposal import ProposalType, StateProposal

from .worker_event import WorkerEvent


@dataclass
class SessionMaintenanceWorker:
    architecture_markers: tuple[str, ...] = ("Context OS", "架构", "State Ownership", "状态归属", "Cognitive Ownership")

    def analyze(self, event: WorkerEvent) -> list[StateProposal]:
        text = _event_text(event)
        if event.event_type != "turn_completed" or not any(marker in text for marker in self.architecture_markers):
            return []
        return [
            StateProposal.create(
                ProposalType.SESSION_STATE_UPDATE,
                source_turn_id=event.source_turn_id,
                summary="Conversation suggests stable session architecture context should be updated.",
                target="open_loop",
                payload={"goal": "Maintain Julia Context OS architecture state", "value": "Julia Context OS / State Ownership"},
                confidence=0.7,
                evidence_refs=[event.source_turn_id],
                metadata={"worker": "session_maintenance", "session_update": {"current_architecture": "Julia Context OS"}},
            )
        ]


def _event_text(event: WorkerEvent) -> str:
    return "\n".join(str(v) for v in event.payload.values() if v is not None)
