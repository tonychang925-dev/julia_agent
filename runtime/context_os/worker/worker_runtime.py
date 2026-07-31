from __future__ import annotations

from dataclasses import dataclass, field

from runtime.context_os.proposal import ProposalValidationResult, ProposalValidator, StateProposal

from .maintenance_job import MaintenanceJob
from .worker_event import WorkerEvent
from .worker_queue import WorkerQueue


@dataclass(frozen=True)
class WorkerRuntimeResult:
    processed_events: list[WorkerEvent]
    proposals: list[StateProposal]
    validation: ProposalValidationResult
    errors: list[str] = field(default_factory=list)


@dataclass
class AsyncContextMaintenanceRuntime:
    """Background cognitive maintenance runtime.

    The synchronous conversation loop only enqueues events. Maintenance may run
    later and returns proposals; it never mutates SessionState/TaskState directly.
    """

    queue: WorkerQueue = field(default_factory=WorkerQueue)
    job: MaintenanceJob = field(default_factory=MaintenanceJob)
    validator: ProposalValidator = field(default_factory=ProposalValidator)

    def submit_turn_completed(self, *, source_turn_id: str, payload: dict[str, object] | None = None) -> None:
        self.queue.enqueue(WorkerEvent.turn_completed(source_turn_id=source_turn_id, payload=dict(payload or {})))

    def enqueue(self, event: WorkerEvent) -> None:
        self.queue.enqueue(event)

    def run_once(self, limit: int | None = None) -> WorkerRuntimeResult:
        events = self.queue.drain(limit=limit)
        proposals: list[StateProposal] = []
        errors: list[str] = []
        for event in events:
            try:
                proposals.extend(self.job.run(event))
            except Exception as exc:  # crash isolation: report and keep loop independent
                errors.append(f"{event.source_turn_id}:{type(exc).__name__}:{exc}")
        validation = self.validator.validate(proposals)
        return WorkerRuntimeResult(processed_events=events, proposals=proposals, validation=validation, errors=errors)
