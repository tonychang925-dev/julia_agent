from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from runtime.context_os.compact import ExperienceCompactState, InMemoryCompactStore
from runtime.context_os.state import JuliaSessionState, JuliaTaskState
from runtime.context_os.transcript import ContextMessageRecord, MessageLifecycleState, ProvenanceType

from .resurrection_request import ResurrectionRequest
from .resurrection_snapshot import ResurrectionSnapshot


class SessionStateStore(Protocol):
    def get_session(self, session_id: str) -> JuliaSessionState | None: ...


class TaskStateStore(Protocol):
    def get_task_for_session(self, session_id: str) -> JuliaTaskState | None: ...


@dataclass
class InMemoryResurrectionSource:
    session_states: dict[str, JuliaSessionState] = field(default_factory=dict)
    task_states: dict[str, JuliaTaskState] = field(default_factory=dict)
    records: list[ContextMessageRecord] = field(default_factory=list)
    compact_store: InMemoryCompactStore = field(default_factory=InMemoryCompactStore)

    def get_session(self, session_id: str) -> JuliaSessionState | None:
        return self.session_states.get(session_id)

    def get_task_for_session(self, session_id: str) -> JuliaTaskState | None:
        for task in self.task_states.values():
            if task.session_id == session_id and task.status in {"active", "doing", "in_progress", "In review", "Todo", "Doing"}:
                return task
        for task in self.task_states.values():
            if task.session_id == session_id:
                return task
        return None

    def list_records_for_session(self, session_id: str) -> list[ContextMessageRecord]:
        return [r for r in self.records if r.session_id == session_id]

    def list_compacts_for_session(self, session_id: str) -> list[ExperienceCompactState]:
        return self.compact_store.list_for_session(session_id)


@dataclass
class ResurrectionLoader:
    source: InMemoryResurrectionSource
    tail_limit: int = 6

    def load(self, request: ResurrectionRequest) -> ResurrectionSnapshot:
        session_id = request.session_id or self._infer_session_id(request)
        if not session_id:
            return ResurrectionSnapshot.create(
                user_id=request.user_id,
                session_id="",
                missing=["session_id", "session_state", "task_state", "compact_state"],
                restoration_confidence=0.0,
            )

        session_state = self.source.get_session(session_id)
        task_state = self.source.get_task_for_session(session_id)
        compact_state = self._latest_compact(session_id)
        recent_tail = self._recent_tail(session_id)
        open_loops = self._open_loops(task_state, compact_state, recent_tail)
        evidence_refs = self._evidence_refs(compact_state, recent_tail)
        sources: list[str] = []
        missing: list[str] = []
        if session_state:
            sources.append("session_state")
        else:
            missing.append("session_state")
        if task_state:
            sources.append("task_state")
        else:
            missing.append("task_state")
        if compact_state:
            sources.append(compact_state.compact_id)
        else:
            missing.append("compact_state")
        sources.extend([r.message_id for r in recent_tail])
        if not recent_tail:
            missing.append("recent_tail")
        confidence = self._confidence(session_state, task_state, compact_state, recent_tail, evidence_refs)
        return ResurrectionSnapshot.create(
            user_id=request.user_id,
            session_id=session_id,
            session_state=session_state,
            task_state=task_state,
            compact_state=compact_state,
            recent_tail=recent_tail,
            active_open_loops=open_loops,
            evidence_refs=evidence_refs,
            restoration_confidence=confidence,
            sources=sources,
            missing=missing,
            metadata={"task_hint": request.task_hint, "target_time": request.target_time},
        )

    def _infer_session_id(self, request: ResurrectionRequest) -> str | None:
        if self.source.session_states:
            return sorted(self.source.session_states.values(), key=lambda s: s.updated_at)[-1].session_id
        compacts = list(self.source.compact_store.compacts.values())
        if compacts:
            return sorted(compacts, key=lambda c: c.created_at)[-1].session_id
        if self.source.records:
            return sorted(self.source.records, key=lambda r: (r.created_at, r.turn_id))[-1].session_id
        return None

    def _latest_compact(self, session_id: str) -> ExperienceCompactState | None:
        compacts = self.source.list_compacts_for_session(session_id)
        if not compacts:
            return None
        return sorted(compacts, key=lambda c: (c.period_end, c.created_at, c.compact_id))[-1]

    def _recent_tail(self, session_id: str) -> list[ContextMessageRecord]:
        records = [
            r for r in self.source.list_records_for_session(session_id)
            if r.lifecycle_state == MessageLifecycleState.ACTIVE and r.provenance_type != ProvenanceType.ASSISTANT_RESPONSE
        ]
        return sorted(records, key=lambda r: (r.turn_id, r.created_at, r.message_id))[-self.tail_limit:]

    @staticmethod
    def _open_loops(task_state: JuliaTaskState | None, compact: ExperienceCompactState | None, tail: list[ContextMessageRecord]) -> list[str]:
        loops: list[str] = []
        if task_state:
            loops.extend(task_state.next_actions)
            loops.extend(task_state.blockers)
        if compact:
            loops.extend(compact.open_loops)
            loops.extend(compact.next_actions)
        for r in tail:
            text = r.content.strip()
            lowered = text.lower()
            if any(term in lowered for term in ["下一步", "继续", "todo", "需要", "pending", "open loop", "open_loop"]):
                loops.append(text)
        return _dedupe(loops)

    @staticmethod
    def _evidence_refs(compact: ExperienceCompactState | None, tail: list[ContextMessageRecord]) -> list[str]:
        refs: list[str] = []
        if compact:
            refs.extend(compact.source_evidence_ids)
            refs.extend(compact.source_record_ids)
        for r in tail:
            refs.extend(r.source_refs)
            refs.append(r.message_id)
        return _dedupe(refs)

    @staticmethod
    def _confidence(
        session_state: JuliaSessionState | None,
        task_state: JuliaTaskState | None,
        compact: ExperienceCompactState | None,
        tail: list[ContextMessageRecord],
        evidence_refs: list[str],
    ) -> float:
        score = 0.0
        if session_state:
            score += 0.25
        if task_state:
            score += 0.25
        if compact:
            score += 0.25 * compact.confidence
        if tail:
            score += 0.15
        if evidence_refs:
            score += 0.10
        return round(min(1.0, score), 4)


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
