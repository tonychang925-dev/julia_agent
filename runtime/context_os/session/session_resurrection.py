from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from runtime.context_os.budget.context_block import ContextBlock
from runtime.context_os.compact.compact_schema import ExperienceCompactState
from runtime.context_os.transcript.message_record import ContextMessageRecord

from .session_snapshot import SessionSnapshot


@dataclass
class SessionResurrectionEngine:
    """Rebuild startup context from compact state plus preserved tail records."""

    max_tail_records: int = 12

    def create_snapshot(
        self,
        *,
        source_session_id: str,
        compacts: Iterable[ExperienceCompactState] = (),
        preserved_records: Iterable[ContextMessageRecord] = (),
    ) -> SessionSnapshot:
        compact_list = list(compacts)
        tail = list(preserved_records)[-self.max_tail_records:]
        latest = compact_list[-1] if compact_list else None
        return SessionSnapshot.create(
            source_session_id=source_session_id,
            compact_ids=[c.compact_id for c in compact_list],
            preserved_record_ids=[r.message_id for r in tail],
            open_loops=list(latest.open_loops if latest else []),
            next_actions=list(latest.next_actions if latest else []),
            current_task=latest.current_task if latest else "",
            main_arc=latest.main_arc if latest else "",
            relationship_context=list(latest.relationship_development if latest else []),
            metadata={
                "compact_count": len(compact_list),
                "preserved_tail_count": len(tail),
                "source_record_ids": [rid for c in compact_list for rid in c.source_record_ids],
            },
        )

    def build_blocks(
        self,
        *,
        snapshot: SessionSnapshot,
        compacts: Iterable[ExperienceCompactState] = (),
        preserved_records: Iterable[ContextMessageRecord] = (),
    ) -> list[ContextBlock]:
        blocks: list[ContextBlock] = []
        compact_by_id = {c.compact_id: c for c in compacts}
        selected_compacts = [compact_by_id[cid] for cid in snapshot.compact_ids if cid in compact_by_id]
        if selected_compacts:
            compact_text = "\n\n---\n\n".join(c.to_context_block_text() for c in selected_compacts)
            blocks.append(ContextBlock(
                block_id=f"session_restore_compact_{snapshot.snapshot_id}",
                block_type="compact_state",
                priority=88,
                content=(
                    "Recovered prior session compact state. Preserve task, relationship, "
                    "and open-loop continuity from this traceable state:\n" + compact_text
                ),
                required=True,
                source_refs=[c.compact_id for c in selected_compacts],
                evidence_ids=[eid for c in selected_compacts for eid in c.source_evidence_ids],
                authority_score=max(c.confidence for c in selected_compacts),
                metadata={"snapshot_id": snapshot.snapshot_id, "source_session_id": snapshot.source_session_id},
            ))
        tail_by_id = {r.message_id: r for r in preserved_records}
        tail = [tail_by_id[rid] for rid in snapshot.preserved_record_ids if rid in tail_by_id]
        if tail:
            content = "\n".join(f"[{r.speaker.value} authority={r.authority_score:.2f}] {r.content}" for r in tail)
            blocks.append(ContextBlock(
                block_id=f"session_restore_tail_{snapshot.snapshot_id}",
                block_type="recent_turns",
                priority=82,
                content="Recovered active tail from previous session:\n" + content,
                required=False,
                source_refs=[r.message_id for r in tail],
                authority_score=max(r.authority_score for r in tail),
                metadata={"snapshot_id": snapshot.snapshot_id, "tail_count": len(tail)},
            ))
        if snapshot.open_loops or snapshot.next_actions:
            parts: list[str] = []
            if snapshot.current_task:
                parts.append(f"Current task: {snapshot.current_task}")
            if snapshot.main_arc:
                parts.append(f"Main arc: {snapshot.main_arc}")
            if snapshot.open_loops:
                parts.append("Open loops:\n" + "\n".join(f"- {x}" for x in snapshot.open_loops))
            if snapshot.next_actions:
                parts.append("Next actions:\n" + "\n".join(f"- {x}" for x in snapshot.next_actions))
            blocks.append(ContextBlock(
                block_id=f"session_restore_open_loops_{snapshot.snapshot_id}",
                block_type="open_loops",
                priority=86,
                content="\n\n".join(parts),
                required=True,
                source_refs=list(snapshot.compact_ids),
                authority_score=0.75,
                metadata={"snapshot_id": snapshot.snapshot_id},
            ))
        return blocks
