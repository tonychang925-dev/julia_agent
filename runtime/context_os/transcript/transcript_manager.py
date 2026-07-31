from __future__ import annotations

from dataclasses import dataclass, field

from .context_boundary import ContextBoundary
from .message_record import ContextMessageRecord
from .message_state import CognitiveRole, MessageLifecycleState
from .turn_lifecycle import TurnLifecycle


@dataclass(frozen=True)
class ContextState:
    session_id: str
    active_records: list[ContextMessageRecord] = field(default_factory=list)
    retrieved_records: list[ContextMessageRecord] = field(default_factory=list)
    boundaries: list[ContextBoundary] = field(default_factory=list)
    identity_records: list[ContextMessageRecord] = field(default_factory=list)
    relationship_records: list[ContextMessageRecord] = field(default_factory=list)
    task_records: list[ContextMessageRecord] = field(default_factory=list)
    open_loop_records: list[ContextMessageRecord] = field(default_factory=list)

    def reconstruct_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "active_record_ids": [r.message_id for r in self.active_records],
            "retrieved_record_ids": [r.message_id for r in self.retrieved_records],
            "boundary_ids": [b.boundary_id for b in self.boundaries],
            "identity": [r.content for r in self.identity_records],
            "relationship": [r.content for r in self.relationship_records],
            "task": [r.content for r in self.task_records],
            "open_loop": [r.content for r in self.open_loop_records],
        }


@dataclass
class TranscriptLifecycleManager:
    """In-memory Conversation Truth Layer manager.

    Persistence is intentionally not introduced here; existing archive remains the
    durable store until Phase 3.6.10.1 storage migration is explicitly designed.
    """

    records: list[ContextMessageRecord] = field(default_factory=list)
    boundaries: list[ContextBoundary] = field(default_factory=list)
    turn_lifecycle: TurnLifecycle = field(default_factory=TurnLifecycle)

    def ingest_turn(
        self,
        *,
        session_id: str,
        turn_id: int,
        user: str,
        assistant: str,
        topics: list[str] | None = None,
    ) -> list[ContextMessageRecord]:
        created = self.turn_lifecycle.records_from_turn(
            session_id=session_id,
            turn_id=turn_id,
            user=user,
            assistant=assistant,
            topics=topics or [],
        )
        self.records.extend(created)
        return created

    def apply_compact_boundary(
        self,
        *,
        session_id: str,
        compress_before_turn: int,
        preserve_last_turns: int = 2,
        compact_id: str | None = None,
    ) -> ContextBoundary:
        session_records = [r for r in self.records if r.session_id == session_id]
        max_turn = max((r.turn_id for r in session_records), default=-1)
        preserve_from_turn = max(max_turn - preserve_last_turns + 1, compress_before_turn)

        updated: list[ContextMessageRecord] = []
        summarized_ids: list[str] = []
        preserved_ids: list[str] = []
        for record in self.records:
            if record.session_id != session_id:
                updated.append(record)
                continue
            if record.turn_id < preserve_from_turn and record.turn_id < compress_before_turn:
                new_record = record.with_state(MessageLifecycleState.COMPRESSED)
                summarized_ids.append(record.message_id)
            else:
                new_record = record.with_state(MessageLifecycleState.ACTIVE)
                preserved_ids.append(record.message_id)
            updated.append(new_record)
        self.records = updated
        boundary = ContextBoundary.create(
            session_id=session_id,
            boundary_type="compact",
            summarized_record_ids=summarized_ids,
            preserved_record_ids=preserved_ids,
            compact_id=compact_id,
            metadata={"compress_before_turn": compress_before_turn, "preserve_last_turns": preserve_last_turns},
        )
        self.boundaries.append(boundary)
        return boundary

    def retrieve_record(self, message_id: str, source_ref: str | None = None) -> ContextMessageRecord:
        for record in self.records:
            if record.message_id == message_id:
                retrieved = record.as_retrieved(source_ref=source_ref)
                self.records.append(retrieved)
                return retrieved
        raise KeyError(f"ContextMessageRecord not found: {message_id}")

    def build_context_state(self, session_id: str) -> ContextState:
        session_records = [r for r in self.records if r.session_id == session_id]
        active = [r for r in session_records if r.lifecycle_state == MessageLifecycleState.ACTIVE]
        retrieved = [r for r in session_records if r.lifecycle_state == MessageLifecycleState.RETRIEVED]
        return ContextState(
            session_id=session_id,
            active_records=active,
            retrieved_records=retrieved,
            boundaries=[b for b in self.boundaries if b.session_id == session_id],
            identity_records=[r for r in active + retrieved if r.cognitive_role == CognitiveRole.IDENTITY],
            relationship_records=[r for r in active + retrieved if r.cognitive_role == CognitiveRole.RELATIONSHIP],
            task_records=[r for r in active + retrieved if r.cognitive_role == CognitiveRole.TASK],
            open_loop_records=[r for r in active + retrieved if r.cognitive_role == CognitiveRole.DECISION],
        )
