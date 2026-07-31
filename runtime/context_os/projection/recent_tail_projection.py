from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from runtime.context_os.transcript.message_record import ContextMessageRecord
from runtime.context_os.transcript.message_state import MessageLifecycleState

from .projection_block import ContextProjectionBlock


@dataclass
class RecentTailProjection:
    max_records: int = 8

    def project(self, records: Iterable[ContextMessageRecord] = ()) -> list[ContextProjectionBlock]:
        active = [r for r in records if r.lifecycle_state == MessageLifecycleState.ACTIVE]
        tail = active[-self.max_records:]
        if not tail:
            return []
        content = "\n".join(f"[{r.speaker.value} authority={r.authority_score:.2f}] {r.content}" for r in tail)
        return [ContextProjectionBlock(
            block_id="projection_recent_tail",
            block_type="recent_turns",
            source_refs=[r.message_id for r in tail],
            content="Recent active conversation tail:\n" + content,
            priority=80,
            authority=max(r.authority_score for r in tail),
            required=False,
            metadata={"projection": "recent_tail", "tail_count": len(tail)},
        )]
