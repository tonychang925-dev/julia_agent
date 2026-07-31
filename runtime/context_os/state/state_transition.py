from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from runtime.context_os.execution.context_mutation import ContextMutation, MutationType

from .session_state import JuliaSessionState
from .task_state import JuliaTaskState


@dataclass(frozen=True)
class SessionTaskStateTransition:
    previous_session: JuliaSessionState | None
    next_session: JuliaSessionState | None
    previous_task: JuliaTaskState | None
    next_task: JuliaTaskState | None
    applied_mutation_ids: list[str]
    rejected_mutation_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["previous_session"] = self.previous_session.to_dict() if self.previous_session else None
        data["next_session"] = self.next_session.to_dict() if self.next_session else None
        data["previous_task"] = self.previous_task.to_dict() if self.previous_task else None
        data["next_task"] = self.next_task.to_dict() if self.next_task else None
        return data


class SessionTaskStateTransitionEngine:
    """Apply authorized context mutations to Session/Task state.

    It deliberately updates working state only. It does not create governed long
    term memory; Async Session Memory Worker may consume the trace later.
    """

    protected_targets = {"identity", "relationship", "persona"}

    def apply(
        self,
        *,
        session_state: JuliaSessionState | None,
        task_state: JuliaTaskState | None,
        mutations: list[ContextMutation],
    ) -> SessionTaskStateTransition:
        next_session = session_state
        next_task = task_state
        applied: list[str] = []
        rejected: list[str] = []
        for mutation in mutations:
            if mutation.target in self.protected_targets:
                rejected.append(mutation.mutation_id)
                continue
            if mutation.mutation_type == MutationType.OPEN_LOOP_CREATED and next_session is not None:
                next_session = next_session.add_goal(str(mutation.value or mutation.reason))
                applied.append(mutation.mutation_id)
                continue
            if mutation.mutation_type == MutationType.TASK_PROGRESS_UPDATE and next_task is not None:
                value = str(mutation.value or mutation.reason)
                next_task = next_task.add_next_action(value) if value else next_task
                if next_task.status == "pending":
                    next_task = next_task.with_status("active")
                applied.append(mutation.mutation_id)
                continue
            if mutation.mutation_type == MutationType.EVIDENCE_GAP_FOUND and next_task is not None:
                next_task = next_task.add_blocker(str(mutation.reason))
                applied.append(mutation.mutation_id)
                continue
            rejected.append(mutation.mutation_id)
        return SessionTaskStateTransition(
            previous_session=session_state,
            next_session=next_session,
            previous_task=task_state,
            next_task=next_task,
            applied_mutation_ids=applied,
            rejected_mutation_ids=rejected,
        )
