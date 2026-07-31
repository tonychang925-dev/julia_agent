from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .message_state import CognitiveRole, MessageLifecycleState, MessageSpeaker


class ProvenanceType(str, Enum):
    EXPLICIT_USER = "explicit_user"
    ASSISTANT_RESPONSE = "assistant_response"
    COMPACT_GENERATED = "compact_generated"
    REFLECTION_GENERATED = "reflection_generated"
    IMPORTED_DIARY = "imported_diary"
    RETRIEVED_EVIDENCE = "retrieved_evidence"
    RUNTIME_EVENT = "runtime_event"


_AUTHORITY_BY_PROVENANCE: dict[ProvenanceType, float] = {
    ProvenanceType.EXPLICIT_USER: 0.9,
    ProvenanceType.ASSISTANT_RESPONSE: 0.3,
    ProvenanceType.COMPACT_GENERATED: 0.7,
    ProvenanceType.REFLECTION_GENERATED: 0.65,
    ProvenanceType.IMPORTED_DIARY: 0.8,
    ProvenanceType.RETRIEVED_EVIDENCE: 0.85,
    ProvenanceType.RUNTIME_EVENT: 0.0,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ContextMessageRecord:
    """Single source of cognitive truth for one message in Context OS.

    This is not merely a transcript row.  It records why the message exists,
    how trustworthy it is, and whether it may still enter model-facing context.
    """

    message_id: str
    session_id: str
    turn_id: int
    speaker: MessageSpeaker
    content: str
    lifecycle_state: MessageLifecycleState = MessageLifecycleState.ACTIVE
    cognitive_role: CognitiveRole = CognitiveRole.CASUAL
    authority_score: float = 0.0
    importance_score: float = 0.0
    topics: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    provenance_type: ProvenanceType = ProvenanceType.EXPLICIT_USER
    parent_records: list[str] = field(default_factory=list)
    derivation_chain: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValueError("message_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if self.turn_id < 0:
            raise ValueError("turn_id must be >= 0")
        if self.authority_score < 0 or self.authority_score > 1:
            raise ValueError("authority_score must be in [0, 1]")
        if self.importance_score < 0 or self.importance_score > 1:
            raise ValueError("importance_score must be in [0, 1]")

    @classmethod
    def create(
        cls,
        *,
        message_id: str,
        session_id: str,
        turn_id: int,
        speaker: MessageSpeaker | str,
        content: str,
        cognitive_role: CognitiveRole | str = CognitiveRole.CASUAL,
        provenance_type: ProvenanceType | str | None = None,
        authority_score: float | None = None,
        importance_score: float = 0.0,
        topics: list[str] | None = None,
        source_refs: list[str] | None = None,
        parent_records: list[str] | None = None,
        derivation_chain: list[str] | None = None,
        lifecycle_state: MessageLifecycleState | str = MessageLifecycleState.ACTIVE,
        metadata: dict[str, Any] | None = None,
    ) -> "ContextMessageRecord":
        speaker_enum = MessageSpeaker(speaker)
        provenance = ProvenanceType(
            provenance_type
            or (
                ProvenanceType.EXPLICIT_USER
                if speaker_enum == MessageSpeaker.USER
                else ProvenanceType.ASSISTANT_RESPONSE
                if speaker_enum == MessageSpeaker.ASSISTANT
                else ProvenanceType.RUNTIME_EVENT
            )
        )
        return cls(
            message_id=message_id,
            session_id=session_id,
            turn_id=turn_id,
            speaker=speaker_enum,
            content=content,
            lifecycle_state=MessageLifecycleState(lifecycle_state),
            cognitive_role=CognitiveRole(cognitive_role),
            authority_score=(
                _AUTHORITY_BY_PROVENANCE[provenance]
                if authority_score is None
                else authority_score
            ),
            importance_score=importance_score,
            topics=list(topics or []),
            source_refs=list(source_refs or []),
            provenance_type=provenance,
            parent_records=list(parent_records or []),
            derivation_chain=list(derivation_chain or [provenance.value]),
            metadata=dict(metadata or {}),
        )

    def with_state(self, state: MessageLifecycleState | str) -> "ContextMessageRecord":
        return replace(
            self,
            lifecycle_state=MessageLifecycleState(state),
            updated_at=utc_now_iso(),
        )

    def as_retrieved(self, source_ref: str | None = None) -> "ContextMessageRecord":
        refs = list(self.source_refs)
        if source_ref and source_ref not in refs:
            refs.append(source_ref)
        return replace(
            self,
            lifecycle_state=MessageLifecycleState.RETRIEVED,
            source_refs=refs,
            updated_at=utc_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["speaker"] = self.speaker.value
        data["lifecycle_state"] = self.lifecycle_state.value
        data["cognitive_role"] = self.cognitive_role.value
        data["provenance_type"] = self.provenance_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextMessageRecord":
        cleaned = dict(data)
        cleaned["speaker"] = MessageSpeaker(cleaned["speaker"])
        cleaned["lifecycle_state"] = MessageLifecycleState(cleaned["lifecycle_state"])
        cleaned["cognitive_role"] = CognitiveRole(cleaned["cognitive_role"])
        cleaned["provenance_type"] = ProvenanceType(cleaned["provenance_type"])
        return cls(**cleaned)
