from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.state import JuliaSessionState, JuliaTaskState

from .resurrection_snapshot import ResurrectionSnapshot


@dataclass(frozen=True)
class RestoredStateView:
    project: str = ""
    phase: str = ""
    current_task: str = ""
    active_goals: list[str] = None
    decisions: list[str] = None
    next_actions: list[str] = None


@dataclass
class StateRestorer:
    """Restores explicit Session/Task state with authority over compact text."""

    def restore(self, snapshot: ResurrectionSnapshot) -> dict[str, object]:
        session: JuliaSessionState | None = snapshot.session_state
        task: JuliaTaskState | None = snapshot.task_state
        compact = snapshot.compact_state
        project_context = session.project_context if session else {}
        project = str(project_context.get("project") or "")
        phase = str(project_context.get("phase") or "")
        current_task = ""
        if task:
            current_task = task.objective
        elif compact:
            current_task = compact.current_task
        decisions: list[str] = []
        if session:
            decisions.extend(session.architecture_decisions)
        if task:
            decisions.extend(task.decisions)
        if compact:
            decisions.extend([d.decision for d in compact.decisions])
        next_actions: list[str] = []
        if task:
            next_actions.extend(task.next_actions)
        if compact:
            next_actions.extend(compact.next_actions)
        return {
            "project": project,
            "phase": phase,
            "current_task": current_task,
            "active_goals": list(session.active_goals if session else []),
            "decisions": _dedupe(decisions),
            "next_actions": _dedupe(next_actions),
        }


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
