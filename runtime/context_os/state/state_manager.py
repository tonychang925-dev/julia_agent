from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from runtime.context_os.budget import ContextBlock
from runtime.context_os.execution.context_mutation import ContextMutation

from .session_state import JuliaSessionState
from .state_projection import SessionTaskStateProjection
from .state_store import ContextStateStore
from .state_transition import SessionTaskStateTransition, SessionTaskStateTransitionEngine
from .task_state import JuliaTaskState


@dataclass
class JuliaStateManager:
    store: ContextStateStore | None = None
    projector: SessionTaskStateProjection = field(default_factory=SessionTaskStateProjection)
    transition_engine: SessionTaskStateTransitionEngine = field(default_factory=SessionTaskStateTransitionEngine)

    @classmethod
    def with_root(cls, root: str | Path) -> "JuliaStateManager":
        return cls(store=ContextStateStore(Path(root)))

    def save(self, *, session_state: JuliaSessionState | None = None, task_state: JuliaTaskState | None = None) -> None:
        if self.store is None:
            return
        if session_state is not None:
            self.store.save_session(session_state)
        if task_state is not None:
            self.store.save_task(task_state)

    def load_session(self, session_id: str) -> JuliaSessionState | None:
        return self.store.load_session(session_id) if self.store else None

    def load_task(self, task_id: str) -> JuliaTaskState | None:
        return self.store.load_task(task_id) if self.store else None

    def project_blocks(self, *, session_state: JuliaSessionState | None = None, task_state: JuliaTaskState | None = None) -> list[ContextBlock]:
        return self.projector.project(session_state=session_state, task_state=task_state)

    def apply_mutations(
        self,
        *,
        session_state: JuliaSessionState | None,
        task_state: JuliaTaskState | None,
        mutations: list[ContextMutation],
        persist: bool = True,
    ) -> SessionTaskStateTransition:
        transition = self.transition_engine.apply(session_state=session_state, task_state=task_state, mutations=mutations)
        if persist:
            self.save(session_state=transition.next_session, task_state=transition.next_task)
        return transition
