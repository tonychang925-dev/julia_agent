from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.cognitive_context import JuliaContext

from .capability_context import CapabilityContext, CapabilityRequest


@dataclass
class CapabilityInvocationPlanner:
    """Simple deterministic planner for Phase 3.4.2.

    Later this can be replaced by LLM tool-call planning, but tool execution must
    still pass through CapabilityRequest + PermissionGuard + Router.
    """

    def plan(self, context: JuliaContext) -> CapabilityRequest | None:
        text = context.current_input
        if any(keyword in text for keyword in ["context builder", "代码", "文件", "检查", "看看"]):
            risk_level = "high" if any(keyword in text for keyword in ["删除", "delete", "remove", "rm"]) else "low"
            return CapabilityRequest(
                capability="claude_code_tool",
                action="handoff",
                input={"task": text, "path_hint": "runtime/cognitive/context_builder.py" if "context builder" in text else None},
                session_id=context.runtime_state.get("session_id"),
                turn_id=context.conversation.get("turn_id"),
                correlation_id=f"{context.runtime_state.get('session_id')}_turn_{context.conversation.get('turn_id')}",
                context=CapabilityContext(
                    session_id=context.runtime_state.get("session_id"),
                    actor="julia_runtime",
                    intent=text,
                    risk_level=risk_level,
                    authorization="user_requested",
                    parent_turn_id=context.conversation.get("turn_id"),
                ),
            )
        return None
