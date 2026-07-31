from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_state import ConversationTurn
from runtime.reflection import ConsolidationPolicy, MemoryCandidate, ReflectionEngine, ReflectionInput
from runtime.situation import SituationContext


def situation() -> SituationContext:
    return SituationContext(
        current_activity="building Julia Reflection Runtime",
        environment="software_architecture",
        goal="autonomous memory consolidation",
        interaction_mode="engineering_collaboration",
        active_topics=["Julia Runtime", "Reflection"],
    )


def reflection_input(turns, *, active_topics=None, arc="technical_progress") -> ReflectionInput:
    return ReflectionInput(
        conversation_arc=arc,
        recent_turns=turns,
        active_topics=active_topics or ["Julia Runtime", "Cognitive Architecture", "Provider Migration"],
        open_loops=[],
        situation_context=situation(),
    )


class Phase36ReflectionRuntimeTests(unittest.TestCase):
    def test_tc_phase36_001_milestone_detection_consolidates_trajectory(self):
        # TC-PHASE36-001
        turns = [
            ConversationTurn(1, "完成 JuliaContext v2。", "这是关键结构。", "2026-07-27", ["Julia Runtime"], "engineering_collaboration"),
            ConversationTurn(2, "完成 Cognitive Mode Arbitration。", "Mode 现在由 Runtime 决定。", "2026-07-27", ["Cognitive Architecture"], "engineering_collaboration"),
            ConversationTurn(3, "完成 Conversation Continuity。", "这补齐时间维度。", "2026-07-27", ["Cognitive Architecture"], "engineering_collaboration"),
        ]

        candidates = ReflectionEngine().reflect(reflection_input(turns))

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].memory_type, "episodic")
        self.assertIn("Julia Runtime", candidates[0].summary)
        self.assertGreaterEqual(candidates[0].importance["technical"], 0.9)
        self.assertGreaterEqual(candidates[0].confidence, 0.9)

    def test_tc_phase36_002_noise_filtering_discards_low_value_turns(self):
        # TC-PHASE36-002
        turns = [ConversationTurn(1, "今天下午喝咖啡。", "听起来不错。", "2026-07-27", [], "private_voice_continuity")]

        candidates = ReflectionEngine().reflect(reflection_input(turns, active_topics=[], arc="ongoing_conversation"))

        self.assertEqual(candidates, [])

    def test_tc_phase36_003_memory_merge_combines_related_runtime_journey(self):
        # TC-PHASE36-003
        left = MemoryCandidate(
            memory_type="episodic",
            summary="Tony started Julia Runtime independence.",
            reason="first milestone",
            importance={"technical": 0.9, "relationship": 0.7, "recurrence": 0.8, "emotional": 0.7},
            confidence=0.82,
            topics=["Julia Runtime", "Provider Migration"],
            source="reflection_runtime",
        )
        right = MemoryCandidate(
            memory_type="episodic",
            summary="Tony completed Cognitive Environment.",
            reason="second milestone",
            importance={"technical": 0.95, "relationship": 0.8, "recurrence": 0.9, "emotional": 0.85},
            confidence=0.92,
            topics=["Julia Runtime", "Cognitive Architecture"],
            source="reflection_runtime",
        )

        merged = ConsolidationPolicy().merge_duplicates([left, right])

        self.assertEqual(len(merged), 1)
        self.assertIn("Independence Journey", merged[0].summary)
        self.assertEqual(merged[0].importance["technical"], 0.95)
        self.assertEqual(merged[0].confidence, 0.92)

    def test_tc_phase36_004_importance_gate_rejects_low_confidence_candidate(self):
        # TC-PHASE36-004
        candidate = MemoryCandidate(
            memory_type="episodic",
            summary="minor item",
            reason="low confidence",
            importance={"technical": 0.9, "relationship": 0.9, "recurrence": 0.9, "emotional": 0.9},
            confidence=0.4,
            topics=["Julia Runtime"],
            source="reflection_runtime",
        )

        self.assertFalse(ConsolidationPolicy().should_store(candidate))
        self.assertEqual(ConsolidationPolicy().filter([candidate]), [])

    def test_tc_phase36_005_runtime_isolation_in_memory_candidate(self):
        # TC-PHASE36-005
        turns = [ConversationTurn(1, "完成 Reflection Runtime。", "进入 Memory Consolidation。", "2026-07-27", ["Julia Runtime"], "engineering_collaboration", metadata={"provider": "deepseek", "latency": 1})]

        candidates = ReflectionEngine().reflect(reflection_input(turns))
        serialized = str(candidates).lower()

        self.assertTrue(candidates)
        for forbidden in ["deepseek-chat", "provider", "backend", "latency", "tts", "session_id"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
