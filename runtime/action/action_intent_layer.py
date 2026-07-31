from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.context_os.invariant import InvariantGuard

from .action_intent import ActionIntent


@dataclass(frozen=True)
class ActionIntentTrace:
    """Explainability trace for controlled agency intent formation."""

    source: str
    context_sources: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "context_sources": list(self.context_sources),
            "evidence_refs": list(self.evidence_refs),
            "open_loops": list(self.open_loops),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ActionIntentProposal:
    """Intent proposal only. It is not a command, capability call, or execution."""

    intent: ActionIntent | None
    trace: ActionIntentTrace
    executable: bool = False
    blocked_reason: str | None = None

    @property
    def has_intent(self) -> bool:
        return self.intent is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent.__dict__ if self.intent else None,
            "trace": self.trace.to_dict(),
            "executable": self.executable,
            "blocked_reason": self.blocked_reason,
        }


@dataclass
class ActionIntentLayer:
    """Build ActionIntent from Context OS JuliaContext.

    This is the first Controlled Agency layer: it can infer what Julia should
    consider doing next, but cannot execute, invoke capabilities, or mutate state.
    """

    invariant_guard: InvariantGuard = field(default_factory=InvariantGuard)

    def infer(self, julia_context: Any, *, user_input: str = "") -> ActionIntentProposal:
        invariant = self.invariant_guard.pre_turn(julia_context, source="action_intent_context")
        trace = ActionIntentTrace(
            source="context_os_julia_context",
            context_sources=list(getattr(julia_context, "sources", []) or []),
            evidence_refs=list(getattr(julia_context, "evidence_refs", []) or []),
            open_loops=list(getattr(julia_context, "open_loops", []) or []),
            reason="intent inferred from reconstructed JuliaContext, not provider output",
        )
        if invariant.blocked:
            return ActionIntentProposal(intent=None, trace=trace, blocked_reason="invariant_guard_blocked")

        current_task = str(getattr(julia_context, "current_task", "") or "")
        phase = str(getattr(julia_context, "phase", "") or "")
        project = str(getattr(julia_context, "project", "") or "")
        open_loops = list(getattr(julia_context, "open_loops", []) or [])
        next_actions = list(getattr(julia_context, "next_actions", []) or [])
        text = "\n".join([user_input, current_task, phase, project, *open_loops, *next_actions]).lower()

        if not current_task and not next_actions and not open_loops:
            return ActionIntentProposal(intent=None, trace=trace, blocked_reason="no_actionable_context")

        intent_type = "continue_task"
        capability = "planning"
        risk = "low"
        goal = current_task or (next_actions[0] if next_actions else open_loops[0])
        reason = "Continue the active Context OS task from restored cognitive state"

        if self._benchmark_signal(text):
            intent_type = "run_context_benchmark"
            capability = "benchmark"
            goal = "run Context OS integration benchmark gate"
            reason = "Context OS benchmark gate is the active next action"
        elif self._inspect_signal(text):
            intent_type = "inspect_repository"
            capability = "code_inspection"
            reason = "Restored context indicates repository or architecture inspection"
        elif self._implement_signal(text):
            intent_type = "implement_phase"
            capability = "code_modification"
            risk = "medium"
            reason = "Restored context indicates the next phase requires implementation"
        elif self._policy_signal(text):
            intent_type = "design_policy"
            capability = "planning"
            reason = "Restored context indicates governance or policy design"

        intent = ActionIntent(
            intent_type=intent_type,
            goal=self._sanitize(goal),
            target="julia_agent" if "julia" in text or "context os" in text else None,
            risk_level=risk,
            required_capability=capability,
            reason=reason,
            confidence=self._confidence(julia_context),
        )
        return ActionIntentProposal(intent=intent, trace=trace)

    @staticmethod
    def _confidence(julia_context: Any) -> float:
        base = float(getattr(julia_context, "confidence", 0.75) or 0.75)
        has_sources = bool(getattr(julia_context, "sources", []) or getattr(julia_context, "evidence_refs", []))
        return round(min(0.98, max(0.5, base + (0.05 if has_sources else 0.0))), 4)

    @staticmethod
    def _sanitize(value: str) -> str:
        forbidden = ["rm ", "curl ", "python ", "git ", "cat ", "ls ", "bash ", "sh "]
        cleaned = str(value).strip()
        lowered = cleaned.lower()
        for token in forbidden:
            if token in lowered:
                cleaned = cleaned.replace(token.strip(), "[command]")
                lowered = cleaned.lower()
        return cleaned[:240]

    @staticmethod
    def _benchmark_signal(text: str) -> bool:
        return "benchmark" in text or "gate" in text or "基准" in text

    @staticmethod
    def _inspect_signal(text: str) -> bool:
        return any(term in text for term in ["inspect", "检查", "review", "架构检查"])

    @staticmethod
    def _implement_signal(text: str) -> bool:
        return any(term in text for term in ["implement", "实现", "新增", "开发"])

    @staticmethod
    def _policy_signal(text: str) -> bool:
        return any(term in text for term in ["policy", "governance", "治理", "边界"])
