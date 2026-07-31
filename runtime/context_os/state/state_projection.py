from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.budget import ContextBlock

from .session_state import JuliaSessionState
from .task_state import JuliaTaskState


def _lines(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [title, *[f"- {item}" for item in items]]


@dataclass
class SessionTaskStateProjection:
    """Project session/task state into model-facing ContextBlocks."""

    def project_session(self, state: JuliaSessionState | None) -> list[ContextBlock]:
        if state is None:
            return []
        context_lines = [f"{key}: {value}" for key, value in state.project_context.items() if not isinstance(value, list)]
        if isinstance(state.project_context.get("design_principles"), list):
            context_lines.extend(_lines("design_principles:", [str(x) for x in state.project_context["design_principles"]]))
        content = "\n".join([
            "Julia Session State",
            *context_lines,
            *_lines("architecture_decisions:", state.architecture_decisions),
            *_lines("persistent_constraints:", state.persistent_constraints),
            *_lines("active_goals:", state.active_goals),
        ]).strip()
        return [ContextBlock(
            block_id=f"session_state_{state.session_id}",
            block_type="session_state",
            priority=88,
            content=content,
            required=False,
            source_refs=[f"session_state:{state.session_id}"],
            authority_score=0.9,
            metadata={"projection": "session_state", "provenance": "runtime_session_state", "conflict_topic": "session_state"},
        )]

    def project_task(self, state: JuliaTaskState | None) -> list[ContextBlock]:
        if state is None:
            return []
        content = "\n".join([
            "Julia Task State",
            f"objective: {state.objective}",
            f"status: {state.status}",
            f"progress: {state.progress:.2f}",
            *_lines("decisions:", state.decisions),
            *_lines("blockers:", state.blockers),
            *_lines("next_actions:", state.next_actions),
        ]).strip()
        return [ContextBlock(
            block_id=f"task_state_{state.task_id}",
            block_type="active_task",
            priority=92,
            content=content,
            required=False,
            source_refs=[f"task_state:{state.task_id}"],
            authority_score=0.88,
            metadata={"projection": "task_state", "provenance": "runtime_task_state", "conflict_topic": "active_task"},
        )]

    def project(self, *, session_state: JuliaSessionState | None = None, task_state: JuliaTaskState | None = None) -> list[ContextBlock]:
        return [*self.project_session(session_state), *self.project_task(task_state)]
