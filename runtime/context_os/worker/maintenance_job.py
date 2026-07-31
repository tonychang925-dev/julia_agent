from __future__ import annotations

from dataclasses import dataclass, field

from runtime.context_os.proposal import StateProposal

from .compact_preparation import CompactPreparationWorker
from .memory_maintenance import MemoryMaintenanceWorker
from .session_maintenance import SessionMaintenanceWorker
from .task_maintenance import TaskMaintenanceWorker
from .worker_event import WorkerEvent


@dataclass
class MaintenanceJob:
    memory_worker: MemoryMaintenanceWorker = field(default_factory=MemoryMaintenanceWorker)
    session_worker: SessionMaintenanceWorker = field(default_factory=SessionMaintenanceWorker)
    task_worker: TaskMaintenanceWorker = field(default_factory=TaskMaintenanceWorker)
    compact_worker: CompactPreparationWorker = field(default_factory=CompactPreparationWorker)

    def run(self, event: WorkerEvent) -> list[StateProposal]:
        proposals: list[StateProposal] = []
        for worker in (self.memory_worker, self.session_worker, self.task_worker, self.compact_worker):
            proposals.extend(worker.analyze(event))
        if event.payload.get("evidence_gap"):
            from runtime.context_os.proposal import ProposalType

            proposals.append(
                StateProposal.create(
                    ProposalType.EVIDENCE_GAP,
                    source_turn_id=event.source_turn_id,
                    summary="Worker detected evidence gap from turn metadata.",
                    target="evidence",
                    payload={"value": str(event.payload.get("evidence_gap"))},
                    confidence=0.8,
                    evidence_refs=[event.source_turn_id],
                    metadata={"worker": "evidence_gap_detector"},
                )
            )
        return proposals
