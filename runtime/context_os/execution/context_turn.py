from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from runtime.context_os.budget.context_block import ContextBlock
from runtime.context_os.planner.context_plan import ContextPlan
from runtime.context_os.quality.context_quality import ContextQuality

from .context_mutation import ContextMutation
from .execution_trace import ExecutionTrace


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ContextTurn:
    turn_id: str
    session_id: str
    user_input: str
    context_plan: ContextPlan
    selected_blocks: list[ContextBlock] = field(default_factory=list)
    quality: ContextQuality | None = None
    provider_request_id: str | None = None
    response: str | None = None
    mutations: list[ContextMutation] = field(default_factory=list)
    trace_id: str | None = None
    created_at: str = field(default_factory=now_iso)
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.turn_id:
            raise ValueError("turn_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.user_input:
            raise ValueError("user_input is required")

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        user_input: str,
        context_plan: ContextPlan,
        selected_blocks: list[ContextBlock] | None = None,
        quality: ContextQuality | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ContextTurn":
        return cls(
            turn_id=f"ctx_turn_{uuid4().hex}",
            session_id=session_id,
            user_input=user_input,
            context_plan=context_plan,
            selected_blocks=list(selected_blocks or []),
            quality=quality,
            metadata=dict(metadata or {}),
        )

    def complete(
        self,
        *,
        response: str,
        mutations: list[ContextMutation],
        trace: ExecutionTrace,
        provider_request_id: str | None = None,
    ) -> "ContextTurn":
        return replace(
            self,
            response=response,
            mutations=list(mutations),
            trace_id=trace.trace_id,
            provider_request_id=provider_request_id,
            completed_at=now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["context_plan"] = self.context_plan.to_dict()
        data["selected_blocks"] = [b.to_dict() for b in self.selected_blocks]
        data["quality"] = self.quality.to_dict() if self.quality else None
        data["mutations"] = [m.to_dict() for m in self.mutations]
        return data
