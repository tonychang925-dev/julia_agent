from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .message_record import ContextMessageRecord, ProvenanceType
from .message_state import CognitiveRole, MessageSpeaker


@dataclass(frozen=True)
class TurnLifecycle:
    """Factory for ContextMessageRecord objects created from one dialogue turn."""

    default_user_importance: float = 0.6
    default_assistant_importance: float = 0.35

    def records_from_turn(
        self,
        *,
        session_id: str,
        turn_id: int,
        user: str,
        assistant: str,
        topics: list[str] | None = None,
        user_role: CognitiveRole = CognitiveRole.EVIDENCE,
        assistant_role: CognitiveRole = CognitiveRole.CASUAL,
    ) -> list[ContextMessageRecord]:
        records: list[ContextMessageRecord] = []
        if user:
            records.append(
                ContextMessageRecord.create(
                    message_id=f"ctx_msg_{session_id}_{turn_id}_user_{uuid4().hex[:8]}",
                    session_id=session_id,
                    turn_id=turn_id,
                    speaker=MessageSpeaker.USER,
                    content=user,
                    cognitive_role=user_role,
                    provenance_type=ProvenanceType.EXPLICIT_USER,
                    authority_score=0.9,
                    importance_score=self.default_user_importance,
                    topics=topics or [],
                )
            )
        if assistant:
            records.append(
                ContextMessageRecord.create(
                    message_id=f"ctx_msg_{session_id}_{turn_id}_assistant_{uuid4().hex[:8]}",
                    session_id=session_id,
                    turn_id=turn_id,
                    speaker=MessageSpeaker.ASSISTANT,
                    content=assistant,
                    cognitive_role=assistant_role,
                    provenance_type=ProvenanceType.ASSISTANT_RESPONSE,
                    authority_score=0.3,
                    importance_score=self.default_assistant_importance,
                    topics=topics or [],
                )
            )
        return records
