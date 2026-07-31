from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .evidence_restorer import EvidenceRestorer
from .resurrection_snapshot import JuliaContext, ResurrectionSnapshot
from .state_restorer import StateRestorer


@dataclass
class ContextReconstructor:
    state_restorer: StateRestorer = field(default_factory=StateRestorer)
    evidence_restorer: EvidenceRestorer = field(default_factory=EvidenceRestorer)

    def reconstruct(self, snapshot: ResurrectionSnapshot) -> JuliaContext:
        state = self.state_restorer.restore(snapshot)
        evidence_refs = self.evidence_restorer.restore(snapshot)
        compact = snapshot.compact_state
        open_loops = list(snapshot.active_open_loops)
        if compact:
            open_loops.extend(compact.open_loops)
        open_loops = _dedupe(open_loops)
        sources = _dedupe(snapshot.sources)
        return JuliaContext(
            context_id=f"julia_context_{uuid4().hex}",
            user_id=snapshot.user_id,
            session_id=snapshot.session_id,
            project=str(state["project"]),
            phase=str(state["phase"]),
            current_task=str(state["current_task"]),
            active_goals=list(state["active_goals"]),
            decisions=list(state["decisions"]),
            open_loops=open_loops,
            next_actions=list(state["next_actions"]),
            evidence_refs=evidence_refs,
            recent_tail=list(snapshot.recent_tail),
            compact_ids=[compact.compact_id] if compact else [],
            sources=sources,
            confidence=snapshot.restoration_confidence,
            metadata={"provider_independent": True, "missing": list(snapshot.missing)},
        )


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
