from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.context_compiler import JuliaContext


@dataclass(frozen=True)
class MemoryScopeDecision:
    scope: str
    allowed_memory: tuple[str, ...]
    blocked_memory: tuple[str, ...]
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "allowed_memory": list(self.allowed_memory),
            "blocked_memory": list(self.blocked_memory),
            "reason": self.reason,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class MemoryScopeClassifier:
    def classify(self, julia_context: JuliaContext | None = None, *, user_input: str = "", cognitive_mode: str | None = None) -> MemoryScopeDecision:
        mode = cognitive_mode or (julia_context.cognitive_mode.mode.name if julia_context else "")
        text = (user_input or (julia_context.user_input if julia_context else "")).lower()
        if mode in {"emotional_support", "private_voice_continuity"} or any(term in text for term in ["累", "难过", "想你", "陪", "情绪"]):
            return MemoryScopeDecision(
                scope="emotional",
                allowed_memory=("relationship", "emotion", "personal_continuity", "behavior_preference"),
                blocked_memory=("debug_log", "archival"),
                reason="emotional_or_relationship_context",
                confidence=0.9,
            )
        if any(term in text for term in ["计划", "下一步", "phase", "路线", "规划"]):
            return MemoryScopeDecision(
                scope="planning",
                allowed_memory=("project", "architecture", "technical", "behavior_preference", "normal_episode"),
                blocked_memory=("intimacy", "private", "unrelated_relationship"),
                reason="planning_context",
                confidence=0.86,
            )
        return MemoryScopeDecision(
            scope="engineering",
            allowed_memory=("project", "architecture", "technical", "normal_episode", "behavior_preference"),
            blocked_memory=("relationship", "intimacy", "private"),
            reason="engineering_collaboration_default",
            confidence=0.84,
        )
