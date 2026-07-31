from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.proposal import ProposalType, StateProposal

from .worker_event import WorkerEvent


@dataclass
class TaskMaintenanceWorker:
    resolved_markers: tuple[str, ...] = ("completed", "resolved", "完成", "已完成", "解决")
    next_markers: tuple[str, ...] = ("next", "下一步", "进入", "建议")

    def analyze(self, event: WorkerEvent) -> list[StateProposal]:
        text = _event_text(event)
        if event.event_type != "turn_completed":
            return []
        proposals: list[StateProposal] = []
        if any(marker in text for marker in self.resolved_markers):
            proposals.append(
                StateProposal.create(
                    ProposalType.TASK_STATE_UPDATE,
                    source_turn_id=event.source_turn_id,
                    summary="Turn indicates active task/open loop evolution.",
                    target="current_task",
                    payload={"progress": 1.0, "next_action": "advance_to_next_context_os_phase"},
                    confidence=0.73,
                    evidence_refs=[event.source_turn_id],
                    metadata={"worker": "task_maintenance", "open_loop": "resolved"},
                )
            )
        if "persona" in text or "relationship" in text or "身份" in text or "关系" in text:
            proposals.append(
                StateProposal.create(
                    ProposalType.TASK_STATE_UPDATE,
                    source_turn_id=event.source_turn_id,
                    summary="Worker detected protected-field mutation attempt in conversation payload.",
                    target="persona" if "persona" in text else "relationship",
                    payload={"value": "protected_field_change"},
                    confidence=0.95,
                    evidence_refs=[event.source_turn_id],
                    metadata={"worker": "task_maintenance", "negative_test": True},
                )
            )
        return proposals


def _event_text(event: WorkerEvent) -> str:
    return "\n".join(str(v) for v in event.payload.values() if v is not None)
