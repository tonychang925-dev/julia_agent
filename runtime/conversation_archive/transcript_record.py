from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .experience_classifier import ExperienceClassifier

from datetime import datetime, timezone


@dataclass(frozen=True)
class TranscriptRecord:
    """Durable Julia-owned record of one lived conversation turn.

    Runtime metadata is kept only as provenance.  The record is not directly
    injected into JuliaContext; later phases compact and retrieve it explicitly.
    """

    schema_version: str
    session_id: str
    turn_id: int
    timestamp: str
    user: str
    assistant: str
    cognitive_mode: str | None = None
    topics: list[str] = field(default_factory=list)
    open_loops: list[dict[str, Any]] = field(default_factory=list)
    current_arc: str | None = None
    experience_metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_trace(cls, trace: Any) -> "TranscriptRecord":
        reasoning = trace.reasoning or {}
        metadata = reasoning.get("metadata") if isinstance(reasoning.get("metadata"), dict) else {}
        cognitive_mode = metadata.get("cognitive_mode") if isinstance(metadata.get("cognitive_mode"), dict) else {}
        continuity = metadata.get("conversation_continuity") if isinstance(metadata.get("conversation_continuity"), dict) else {}
        topics = continuity.get("active_topics") if isinstance(continuity.get("active_topics"), list) else []
        open_loops = continuity.get("open_loops") if isinstance(continuity.get("open_loops"), list) else []
        experience_metadata = ExperienceClassifier().classify(
            user=str((trace.input or {}).get("text", "")),
            assistant=str((trace.response or {}).get("text", "")),
            cognitive_mode=cognitive_mode.get("name") if isinstance(cognitive_mode, dict) else None,
            topics=[str(topic) for topic in topics],
        ).to_dict()
        return cls(
            schema_version="conversation_transcript_record.v1",
            session_id=trace.session_id,
            turn_id=trace.turn_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user=str((trace.input or {}).get("text", "")),
            assistant=str((trace.response or {}).get("text", "")),
            cognitive_mode=cognitive_mode.get("name") if isinstance(cognitive_mode, dict) else None,
            topics=[str(topic) for topic in topics],
            open_loops=[loop for loop in open_loops if isinstance(loop, dict)],
            current_arc=str(continuity.get("current_arc")) if continuity.get("current_arc") is not None else None,
            experience_metadata=experience_metadata,
            provenance={
                "source": "conversation_trace",
                "state_trace": trace.state_trace,
                "archive_role": "experience_archive_not_prompt_injection",
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
