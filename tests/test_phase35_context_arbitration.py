from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.arbitration import (
    ArbitrationContext,
    ContextArbitrator,
)
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.relationship import RelationshipContext
from runtime.situation import SituationContext


def relationship(mode: str = "private_voice_continuity") -> RelationshipContext:
    return RelationshipContext(
        user_name="Tony",
        relationship_stage="long_term_collaboration",
        shared_projects=["Julia Runtime"],
        interaction_preferences=["warm", "technical_when_needed"],
        current_mode=mode,
    )


def situation(mode: str = "engineering_collaboration") -> SituationContext:
    return SituationContext(
        current_activity="building Julia Runtime",
        environment="software_architecture",
        goal="reconstruct cognitive environment",
        interaction_mode=mode,
        active_topics=["Julia Runtime", "Context Arbitration"],
    )


def arb_context(**kwargs) -> ArbitrationContext:
    values = {
        "relationship_context": relationship(),
        "situation_context": situation(),
        "conversation_context": {},
        "recent_turns": [],
        "user_intent": {},
    }
    values.update(kwargs)
    return ArbitrationContext(**values)


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase3510",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase35ContextArbitrationTests(unittest.TestCase):
    def test_tc_phase3510_001_explicit_user_intent_has_highest_priority(self):
        result = ContextArbitrator().decide(
            arb_context(
                conversation_context={"active_task_type": "architecture"},
                user_intent={"mode": "emotional_support", "confidence": 0.91},
            )
        )

        self.assertEqual(result.mode.name, "emotional_support")
        self.assertEqual(result.confidence, 0.91)
        self.assertTrue(result.evidence)
        self.assertIn("Explicit user intent", result.reason)

    def test_tc_phase3510_002_active_task_overrides_relationship_mode(self):
        result = ContextArbitrator().decide(
            arb_context(conversation_context={"active_task_type": "debugging"})
        )

        self.assertEqual(result.mode.name, "debugging_mode")
        self.assertIn("active_task_type=debugging", result.evidence)
        self.assertIn("priority", result.reason)

    def test_tc_phase3510_003_conversation_continuity_overrides_relationship_fallback(self):
        result = ContextArbitrator().decide(
            arb_context(
                conversation_context={"recent_cognitive_mode": "learning_mode"},
                recent_turns=[{"user": "这个概念是什么", "assistant": "我慢慢讲。"}],
            )
        )

        self.assertEqual(result.mode.name, "learning_mode")
        self.assertTrue(any(item.startswith("recent_cognitive_mode=") for item in result.evidence))

    def test_tc_phase3510_004_relationship_context_is_fallback_not_persona_change(self):
        result = ContextArbitrator().decide(arb_context())

        self.assertEqual(result.mode.name, "private_voice_continuity")
        self.assertIn("relationship_current_mode=private_voice_continuity", result.evidence)

    def test_tc_phase3510_005_context_compiler_outputs_julia_context_v3(self):
        turn = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
            envelope(),
            "帮我检查 ContextCompiler 架构。",
            conversation_context={"active_task_type": "architecture"},
        )
        context = turn.julia_context

        self.assertEqual(context.cognitive_mode.mode.name, "engineering_collaboration")
        self.assertTrue(context.cognitive_mode.evidence)
        self.assertTrue(context.cognitive_mode.reason)
        self.assertEqual(context.persona_context.name, "Julia")
        self.assertNotIn("deepseek-chat", str(context).lower())

    def test_tc_phase3510_006_no_keyword_dependency_for_same_intent(self):
        arbitrator = ContextArbitrator()
        a = arbitrator.decide(arb_context(user_intent={"mode": "emotional_support"}))
        b = arbitrator.decide(arb_context(user_intent={"mode": "emotional_support"}))

        self.assertEqual(a.mode.name, b.mode.name)
        self.assertEqual(a.reason, b.reason)


if __name__ == "__main__":
    unittest.main()
