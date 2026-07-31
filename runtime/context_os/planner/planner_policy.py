from __future__ import annotations

from dataclasses import dataclass

from .context_intent import ContextIntentType
from .evidence_intent import EvidenceIntentType


@dataclass(frozen=True)
class PlannerDecision:
    intent_type: ContextIntentType
    required_blocks: list[str]
    optional_blocks: list[str]
    evidence_intents: list[EvidenceIntentType]
    excluded_blocks: list[str]
    target_budget_tokens: int
    confidence: float
    reason: str


@dataclass(frozen=True)
class PlannerPolicy:
    """Rule-light semantic planner policy.

    This is not a keyword-to-file retriever.  Lexical cues only classify the
    abstract information need; downstream evidence retrieval resolves concrete
    sources such as Xiaohongshu diary chunks.
    """

    default_budget_tokens: int = 12000

    def decide(self, query: str, cognitive_mode: str) -> PlannerDecision:
        normalized = query.lower().strip()

        if self._is_identity_question(normalized):
            return PlannerDecision(
                intent_type=ContextIntentType.IDENTITY_QUESTION,
                required_blocks=["core_identity", "relationship_anchor"],
                optional_blocks=["semantic_evidence", "compact_state"],
                evidence_intents=[EvidenceIntentType.IDENTITY_ANCHOR, EvidenceIntentType.RELATIONSHIP_ORIGIN],
                excluded_blocks=["runtime_trace"],
                target_budget_tokens=self.default_budget_tokens,
                confidence=0.88,
                reason="Query asks who Julia/Tony is; preserve identity and relationship anchors.",
            )

        if self._is_current_task_question(normalized):
            return PlannerDecision(
                intent_type=ContextIntentType.CURRENT_TASK_QUESTION,
                required_blocks=["core_identity", "relationship_anchor", "active_task"],
                optional_blocks=["recent_turns", "open_loops", "compact_state"],
                evidence_intents=[EvidenceIntentType.PROJECT_STATE, EvidenceIntentType.OPEN_LOOP, EvidenceIntentType.RECENT_CONVERSATION],
                excluded_blocks=["runtime_trace"],
                target_budget_tokens=self.default_budget_tokens,
                confidence=0.86,
                reason="Query asks current work/next step; construct task and open-loop context.",
            )

        if self._is_personal_history_recall(normalized):
            return PlannerDecision(
                intent_type=ContextIntentType.PERSONAL_HISTORY_RECALL,
                required_blocks=["core_identity", "relationship_anchor"],
                optional_blocks=["semantic_evidence", "recent_turns", "compact_state"],
                evidence_intents=[
                    EvidenceIntentType.SHARED_STORY,
                    EvidenceIntentType.CREATIVE_WORK,
                    EvidenceIntentType.LIFE_EXPERIENCE,
                    EvidenceIntentType.RELATIONSHIP_ORIGIN,
                ],
                excluded_blocks=["runtime_trace", "assistant_generated_claims"],
                target_budget_tokens=self.default_budget_tokens,
                confidence=0.82,
                reason="Query asks for a shared prior life/story/creative experience; request abstract evidence types, not keywords.",
            )

        if self._is_technical_debug(normalized):
            return PlannerDecision(
                intent_type=ContextIntentType.TECHNICAL_DEBUG,
                required_blocks=["core_identity", "active_task"],
                optional_blocks=["recent_turns", "semantic_evidence", "known_failures"],
                evidence_intents=[EvidenceIntentType.TECHNICAL_EVIDENCE, EvidenceIntentType.PROJECT_STATE],
                excluded_blocks=["relationship_smalltalk"],
                target_budget_tokens=int(self.default_budget_tokens * 1.25),
                confidence=0.78,
                reason="Query appears to require technical evidence and recent failure context.",
            )

        if self._is_emotional_support(normalized, cognitive_mode):
            return PlannerDecision(
                intent_type=ContextIntentType.EMOTIONAL_SUPPORT,
                required_blocks=["core_identity", "relationship_anchor"],
                optional_blocks=["recent_turns", "emotional_context"],
                evidence_intents=[EvidenceIntentType.EMOTIONAL_CONTEXT, EvidenceIntentType.RECENT_CONVERSATION],
                excluded_blocks=["runtime_trace", "large_technical_logs"],
                target_budget_tokens=int(self.default_budget_tokens * 0.75),
                confidence=0.78,
                reason="Query or mode indicates emotional support; prioritize relationship continuity and recent affect.",
            )

        return PlannerDecision(
            intent_type=ContextIntentType.CASUAL,
            required_blocks=["core_identity", "relationship_anchor"],
            optional_blocks=["recent_turns"],
            evidence_intents=[EvidenceIntentType.RECENT_CONVERSATION],
            excluded_blocks=["runtime_trace"],
            target_budget_tokens=int(self.default_budget_tokens * 0.7),
            confidence=0.55,
            reason="No strong specialized intent detected; use lightweight conversational context.",
        )

    @staticmethod
    def _is_identity_question(q: str) -> bool:
        return any(phrase in q for phrase in ["你是谁", "julia是谁", "认识tony", "tony是谁", "怎么认识tony"])

    @staticmethod
    def _is_current_task_question(q: str) -> bool:
        return any(phrase in q for phrase in ["忙什么", "在做什么", "下一步", "继续", "当前任务", "现在做"])

    @staticmethod
    def _is_personal_history_recall(q: str) -> bool:
        # These cues classify a broad shared-history intent. They must not map to
        # concrete retrieval paths; no file names or diary section names are emitted.
        return any(
            phrase in q
            for phrase in [
                "小红书",
                "文章",
                "故事",
                "以前写",
                "以前分享",
                "给你看",
                "重生",
                "人生",
                "还记得",
                "有印象",
                "那些东西",
            ]
        )

    @staticmethod
    def _is_technical_debug(q: str) -> bool:
        return any(phrase in q for phrase in ["bug", "报错", "日志", "测试", "实现", "代码", "接口", "架构", "模块"])

    @staticmethod
    def _is_emotional_support(q: str, mode: str) -> bool:
        return mode in {"emotional_support", "private_voice_continuity"} or any(
            phrase in q for phrase in ["累", "难过", "陪我", "情人模式", "想你"]
        )
