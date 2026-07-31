from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.planner.context_intent import ContextIntentType
from runtime.context_os.quality.context_quality import ContextQuality

from .context_mutation import ContextMutation, MutationType
from .context_turn import ContextTurn


@dataclass
class PostTurnProcessor:
    """Deterministic first-pass post-turn analyzer.

    It creates working-context mutations only. It must not form long-term
    MemoryObject directly; Async Session Memory Worker consumes these traces later.
    """

    def process(self, *, turn: ContextTurn, response: str) -> list[ContextMutation]:
        mutations: list[ContextMutation] = []
        plan = turn.context_plan
        if plan.intent_type in {ContextIntentType.PLANNING, ContextIntentType.TECHNICAL_DEBUG, ContextIntentType.CURRENT_TASK_QUESTION}:
            mutations.append(ContextMutation.create(
                MutationType.TASK_PROGRESS_UPDATE,
                f"Turn focused on {plan.intent_type.value}.",
                target="current_task",
                value=plan.intent_type.value,
                authority_score=0.75,
                source_turn_id=turn.turn_id,
            ))
        if plan.intent_type == ContextIntentType.EMOTIONAL_SUPPORT:
            mutations.append(ContextMutation.create(
                MutationType.CURRENT_ARC_UPDATE,
                "User expressed emotional/support context; current arc should preserve emotional continuity.",
                target="current_arc",
                value="emotional_support",
                authority_score=0.8,
                source_turn_id=turn.turn_id,
            ))
        if plan.intent_type == ContextIntentType.PRIVATE_VOICE_CONTINUITY:
            mutations.append(ContextMutation.create(
                MutationType.COGNITIVE_MODE_CHANGED,
                "Turn requested private voice continuity mode.",
                target="cognitive_mode",
                value="private_voice_continuity",
                authority_score=0.8,
                source_turn_id=turn.turn_id,
            ))
        if plan.intent_type == ContextIntentType.PLANNING or "下一步" in turn.user_input or "继续" in turn.user_input:
            mutations.append(ContextMutation.create(
                MutationType.OPEN_LOOP_CREATED,
                "Planning/continuation turn creates or refreshes an open loop.",
                target="open_loop",
                value=turn.user_input,
                authority_score=0.7,
                source_turn_id=turn.turn_id,
            ))
        self._append_quality_mutations(turn.quality, turn.turn_id, mutations)
        return mutations

    @staticmethod
    def _append_quality_mutations(quality: ContextQuality | None, turn_id: str, mutations: list[ContextMutation]) -> None:
        if quality is None:
            return
        if quality.evidence_count == 0 and quality.hallucination_risk >= 0.6:
            mutations.append(ContextMutation.create(
                MutationType.EVIDENCE_GAP_FOUND,
                "Context quality found no reliable evidence for a high-risk turn.",
                target="evidence",
                value="missing",
                authority_score=0.9,
                source_turn_id=turn_id,
                metadata={"hallucination_risk": quality.hallucination_risk},
            ))
        for warning in quality.warnings:
            mutations.append(ContextMutation.create(
                MutationType.QUALITY_WARNING,
                warning,
                target="context_quality",
                authority_score=0.85,
                source_turn_id=turn_id,
            ))
