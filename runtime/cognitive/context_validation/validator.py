from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from runtime.cognitive.context_compiler import JuliaContext

from .context_quality import ContextQualityReport


class ContextValidator:
    """Validates JuliaContext v3 quality before renderer/provider usage."""

    FORBIDDEN_KEYS = {"provider", "backend", "latency", "tts", "session_id", "turn_id", "model"}
    FORBIDDEN_VALUE_FRAGMENTS = {"deepseek-chat", "claude-code", "current_backend", "latency_target_ms"}

    def __init__(self, *, max_memory_items: int = 8):
        self.max_memory_items = max_memory_items

    def validate(self, context: JuliaContext) -> ContextQualityReport:
        errors: list[str] = []
        warnings: list[str] = []
        conversation_active_topic_count = (
            len(context.conversation_context.active_topics)
            if hasattr(context.conversation_context, "active_topics")
            else 0
        )
        conversation_open_loop_count = (
            len(context.conversation_context.open_loops)
            if hasattr(context.conversation_context, "open_loops")
            else 0
        )
        metrics: dict[str, Any] = {
            "memory_count": len(context.memory_context),
            "memory_types": sorted({memory.type for memory in context.memory_context}),
            "active_topic_count": len(context.situation_context.active_topics),
            "cognitive_mode": context.cognitive_mode.mode.name,
            "cognitive_mode_confidence": context.cognitive_mode.confidence,
            "conversation_active_topic_count": conversation_active_topic_count,
            "conversation_open_loop_count": conversation_open_loop_count,
        }

        self._check_identity(context, errors)
        self._check_relationship(context, errors)
        self._check_memory(context, errors)
        self._check_situation(context, errors, warnings)
        self._check_cognitive_mode(context, errors)
        self._check_conversation_continuity(context, errors)
        self._check_runtime_contamination(context, errors)

        return ContextQualityReport(
            passed=not errors,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    @staticmethod
    def _check_identity(context: JuliaContext, errors: list[str]) -> None:
        if not context.persona_context.name.strip():
            errors.append("identity.name_missing")
        if context.persona_context.name != "Julia":
            errors.append("identity.name_not_julia")
        if not context.persona_context.identity_summary.strip():
            errors.append("identity.summary_missing")

    @staticmethod
    def _check_relationship(context: JuliaContext, errors: list[str]) -> None:
        if context.relationship_context.user_name != "Tony":
            errors.append("relationship.user_not_tony")
        if not context.relationship_context.relationship_stage.strip():
            errors.append("relationship.stage_missing")

    def _check_memory(self, context: JuliaContext, errors: list[str]) -> None:
        if len(context.memory_context) > self.max_memory_items:
            errors.append("memory.too_many_items")
        for index, memory in enumerate(context.memory_context):
            if memory.type not in {"episodic", "semantic", "relationship", "working"}:
                errors.append(f"memory.{index}.invalid_type")
            if not memory.summary.strip():
                errors.append(f"memory.{index}.summary_missing")
            missing_importance = {"emotional", "relationship", "technical", "recurrence"}.difference(memory.importance)
            if missing_importance:
                errors.append(f"memory.{index}.importance_missing:{','.join(sorted(missing_importance))}")

    @staticmethod
    def _check_situation(context: JuliaContext, errors: list[str], warnings: list[str]) -> None:
        situation = context.situation_context
        if not situation.current_activity.strip():
            errors.append("situation.current_activity_missing")
        if not situation.interaction_mode.strip():
            errors.append("situation.interaction_mode_missing")
        if situation.interaction_mode == "engineering_collaboration" and context.memory_context:
            has_technical = any(
                memory.type == "semantic"
                or memory.importance.get("technical", 0.0) >= 0.7
                or any("architecture" in topic.lower() or "runtime" in topic.lower() for topic in memory.topics)
                for memory in context.memory_context
            )
            if not has_technical:
                warnings.append("situation.memory_mismatch:engineering_without_technical_memory")

    @staticmethod
    def _check_cognitive_mode(context: JuliaContext, errors: list[str]) -> None:
        mode = context.cognitive_mode
        if not mode.mode.name.strip():
            errors.append("cognitive_mode.name_missing")
        if mode.confidence < 0.0 or mode.confidence > 1.0:
            errors.append("cognitive_mode.confidence_out_of_range")
        if not mode.evidence:
            errors.append("cognitive_mode.evidence_missing")
        if not mode.reason.strip():
            errors.append("cognitive_mode.reason_missing")

    @staticmethod
    def _check_conversation_continuity(context: JuliaContext, errors: list[str]) -> None:
        conversation = context.conversation_context
        if not hasattr(conversation, "current_arc"):
            errors.append("conversation.invalid_context")
            return
        if not conversation.current_arc.strip():
            errors.append("conversation.current_arc_missing")
        if len(conversation.active_topics) > 8:
            errors.append("conversation.too_many_active_topics")

    def _check_runtime_contamination(self, context: JuliaContext, errors: list[str]) -> None:
        contamination = self._find_contamination(asdict(context) if is_dataclass(context) else context)
        for item in contamination:
            errors.append(f"runtime_contamination:{item}")

    @staticmethod
    def _allowed_conversation_state_key(path: str, key: str) -> bool:
        # ConversationTurn.turn_id is cognitive ordering metadata inside
        # ConversationContinuityContext, not provider/backend/runtime execution
        # metadata. It is not rendered by CognitiveProjection.to_recent_dict().
        return key == "turn_id" and ".conversation_context.recent_turns[" in path

    def _find_contamination(self, value: Any, *, path: str = "context") -> list[str]:
        found: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                key_lower = key_text.lower()
                current_path = f"{path}.{key_text}"
                if key_lower in self.FORBIDDEN_KEYS and not self._allowed_conversation_state_key(current_path, key_lower):
                    found.append(current_path)
                found.extend(self._find_contamination(item, path=current_path))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                found.extend(self._find_contamination(item, path=f"{path}[{index}]"))
        elif isinstance(value, str):
            lower = value.lower()
            for fragment in self.FORBIDDEN_VALUE_FRAGMENTS:
                if fragment.lower() in lower:
                    found.append(path)
                    break
        return found
