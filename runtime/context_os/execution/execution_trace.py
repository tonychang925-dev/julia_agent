from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from runtime.context_os.quality.context_quality import ContextQuality

from .context_mutation import ContextMutation


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ExecutionTrace:
    trace_id: str
    turn_id: str
    session_id: str
    plan_id: str
    context_block_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    excluded_sources: list[str] = field(default_factory=list)
    budget_trace: dict[str, Any] = field(default_factory=dict)
    quality: ContextQuality | None = None
    provider_request_id: str | None = None
    provider_latency_ms: int | None = None
    mutation_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise ValueError("trace_id is required")
        if not self.turn_id:
            raise ValueError("turn_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.plan_id:
            raise ValueError("plan_id is required")
        if self.provider_latency_ms is not None and self.provider_latency_ms < 0:
            raise ValueError("provider_latency_ms must be >= 0")

    @classmethod
    def create(
        cls,
        *,
        turn_id: str,
        session_id: str,
        plan_id: str,
        context_block_ids: list[str],
        evidence_refs: list[str],
        excluded_sources: list[str] | None = None,
        budget_trace: dict[str, Any] | None = None,
        quality: ContextQuality | None = None,
        provider_request_id: str | None = None,
        provider_latency_ms: int | None = None,
        mutations: list[ContextMutation] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ExecutionTrace":
        return cls(
            trace_id=f"ctx_trace_{uuid4().hex}",
            turn_id=turn_id,
            session_id=session_id,
            plan_id=plan_id,
            context_block_ids=list(context_block_ids),
            evidence_refs=list(evidence_refs),
            excluded_sources=list(excluded_sources or []),
            budget_trace=dict(budget_trace or {}),
            quality=quality,
            provider_request_id=provider_request_id,
            provider_latency_ms=provider_latency_ms,
            mutation_ids=[m.mutation_id for m in mutations or []],
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["quality"] = self.quality.to_dict() if self.quality else None
        return data
