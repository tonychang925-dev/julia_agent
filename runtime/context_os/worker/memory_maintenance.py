from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.proposal import ProposalType, StateProposal

from .worker_event import WorkerEvent


@dataclass
class MemoryMaintenanceWorker:
    milestone_markers: tuple[str, ...] = ("milestone", "里程碑", "完成", "Phase", "Context OS", "长期项目")

    def analyze(self, event: WorkerEvent) -> list[StateProposal]:
        text = _event_text(event)
        if event.event_type != "turn_completed" or not any(marker in text for marker in self.milestone_markers):
            return []
        return [
            StateProposal.create(
                ProposalType.MEMORY_CANDIDATE,
                source_turn_id=event.source_turn_id,
                summary="Conversation indicates a durable project milestone or long-lived architectural memory.",
                target="memory",
                payload={"memory_type": "PROJECT_MILESTONE", "value": _clip(text)},
                confidence=0.72,
                evidence_refs=[event.source_turn_id],
                metadata={"worker": "memory_maintenance"},
            )
        ]


def _event_text(event: WorkerEvent) -> str:
    return "\n".join(str(v) for v in event.payload.values() if v is not None)


def _clip(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
