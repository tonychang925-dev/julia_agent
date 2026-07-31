from __future__ import annotations

from .arbitration_context import ArbitrationContext
from .arbitration_result import ArbitrationResult
from .cognitive_mode import (
    DEBUGGING_MODE,
    EMOTIONAL_SUPPORT,
    ENGINEERING_COLLABORATION,
    LEARNING_MODE,
    PLANNING_MODE,
    PRIVATE_VOICE_CONTINUITY,
    mode_by_name,
)


class ContextArbitrator:
    """Decides Julia's cognitive mode from runtime evidence, not provider output."""

    def decide(self, context: ArbitrationContext) -> ArbitrationResult:
        explicit = self._explicit_intent(context)
        if explicit is not None:
            return explicit
        task = self._active_task(context)
        if task is not None:
            return task
        continuity = self._conversation_continuity(context)
        if continuity is not None:
            return continuity
        relationship = self._relationship_context(context)
        if relationship is not None:
            return relationship
        return ArbitrationResult(
            mode=ENGINEERING_COLLABORATION,
            confidence=0.55,
            evidence=["default mode after no higher-priority arbitration evidence matched"],
            reason="No explicit intent, active task, continuity, or relationship-mode evidence overrode the default.",
        )

    def _explicit_intent(self, context: ArbitrationContext) -> ArbitrationResult | None:
        value = context.user_intent.get("mode") or context.user_intent.get("cognitive_mode")
        if value:
            mode = mode_by_name(str(value))
            return ArbitrationResult(
                mode=mode,
                confidence=float(context.user_intent.get("confidence", 0.96)),
                evidence=["explicit user_intent.mode provided by Conversation Understanding"],
                reason="Explicit user intent has highest arbitration priority.",
            )

        text = str(context.user_intent.get("text") or context.user_intent.get("user_input") or "")
        lowered = text.lower()
        emotional_markers = ["累", "疲惫", "撑不住", "难受", "压力", "消耗", "想休息", "有点烦"]
        relationship_markers = ["情感模式", "情人", "陪我", "亲密", "感动", "你还在吗"]
        if any(marker in lowered for marker in emotional_markers):
            return ArbitrationResult(
                mode=EMOTIONAL_SUPPORT,
                confidence=0.92,
                evidence=["explicit_emotional_expression", "user_input_semantic_intent"],
                reason="User expressed fatigue or personal emotional state; this overrides recent engineering mode carryover.",
            )
        if any(marker in lowered for marker in relationship_markers):
            return ArbitrationResult(
                mode=PRIVATE_VOICE_CONTINUITY,
                confidence=0.9,
                evidence=["explicit_relationship_continuation", "user_input_semantic_intent"],
                reason="User asked about relationship/emotional continuity; this overrides recent engineering mode carryover.",
            )
        return None

    def _active_task(self, context: ArbitrationContext) -> ArbitrationResult | None:
        task_type = str(context.conversation_context.get("active_task_type") or context.user_intent.get("task_type") or "")
        mapping = {
            "debugging": DEBUGGING_MODE,
            "bugfix": DEBUGGING_MODE,
            "architecture": ENGINEERING_COLLABORATION,
            "engineering": ENGINEERING_COLLABORATION,
            "learning": LEARNING_MODE,
            "planning": PLANNING_MODE,
        }
        mode = mapping.get(task_type)
        if mode is None:
            return None
        return ArbitrationResult(
            mode=mode,
            confidence=0.9,
            evidence=[f"active_task_type={task_type}"],
            reason="Active task situation has priority over general relationship context.",
        )

    def _conversation_continuity(self, context: ArbitrationContext) -> ArbitrationResult | None:
        recent_mode = str(context.conversation_context.get("recent_cognitive_mode") or "")
        if not recent_mode:
            return None
        mode = mode_by_name(recent_mode)
        return ArbitrationResult(
            mode=mode,
            confidence=0.78,
            evidence=[f"recent_cognitive_mode={recent_mode}", f"recent_turn_count={len(context.recent_turns)}"],
            reason="Recent conversation mode carries forward when no explicit intent or active task overrides it.",
        )

    def _relationship_context(self, context: ArbitrationContext) -> ArbitrationResult | None:
        mode_name = str(context.relationship_context.current_mode or "")
        if not mode_name:
            return None
        mode = mode_by_name(mode_name)
        return ArbitrationResult(
            mode=mode,
            confidence=0.7,
            evidence=[f"relationship_current_mode={mode_name}"],
            reason="Relationship Runtime supplied the standing interaction mode after higher-priority evidence did not override it.",
        )
