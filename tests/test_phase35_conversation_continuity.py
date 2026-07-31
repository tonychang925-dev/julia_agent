from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.conversation_state import ConversationTurn, ContinuityManager, ConversationContinuityContext


def envelope(turn_id: int = 1) -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase3511",
        turn_id=turn_id,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase35ConversationContinuityTests(unittest.TestCase):
    def test_tc_phase3511_001_arc_continuity_tracks_project_pressure(self):
        # TC-PHASE3511-001
        manager = ContinuityManager()
        state = None
        turns = [
            ConversationTurn(1, "我最近压力很大", "发生什么了？", "2026-07-27T00:00:00Z", ["Project Pressure"], "emotional_support"),
            ConversationTurn(2, "项目做不完", "我们可以拆一下。", "2026-07-27T00:01:00Z", ["Project Pressure"], "emotional_support"),
            ConversationTurn(3, "算了继续吧", "我在，继续。", "2026-07-27T00:02:00Z", ["Project Pressure"], "engineering_collaboration"),
        ]
        for turn in turns:
            state = manager.update(state, turn)

        self.assertEqual(state.current_arc, "project_pressure")
        self.assertIn("Project Pressure", state.active_topics)
        self.assertTrue(any(loop.get("topic") == "project_completion" for loop in state.open_loops))
        self.assertIn("project_pressure", state.session_summary)

    def test_tc_phase3511_002_pronoun_reference_uses_recent_active_topic(self):
        # TC-PHASE3511-002
        previous = ConversationContinuityContext(
            active_topics=["Cognitive Architecture", "Context Arbitration"],
            open_loops=[{"topic": "Context Arbitration", "status": "open", "importance": 0.7}],
            current_arc="technical_progress",
            recent_turns=[
                ConversationTurn(1, "Context Arbitration 方案先这样。", "好。", "2026-07-27T00:00:00Z", ["Context Arbitration"], "engineering_collaboration")
            ],
            session_summary="Current conversation arc: technical_progress.",
        )
        state = ContinuityManager().build_context(previous_state=previous, current_user_input="那个方案怎么办？")

        self.assertEqual(state.current_arc, "technical_progress")
        self.assertIn("Context Arbitration", state.active_topics)
        self.assertTrue(any(loop.get("topic") in {"Context Arbitration", "conversation_followup"} for loop in state.open_loops))

    def test_tc_phase3511_003_topic_switch_keeps_topics_bounded(self):
        # TC-PHASE3511-003
        manager = ContinuityManager(max_active_topics=4)
        state = None
        for index, text in enumerate([
            "帮我检查 Julia Runtime 架构。",
            "最近身体状态也不太好，忙完再检查。",
            "回到刚才技术问题，Context Compiler 怎么接？",
        ], start=1):
            topics = manager.topic_tracker.extract_topics(text)
            state = manager.update(state, ConversationTurn(index, text, "收到。", "2026-07-27", topics, "engineering_collaboration"))

        self.assertLessEqual(len(state.active_topics), 4)
        self.assertIn("Health Follow-up", state.active_topics)
        self.assertTrue(any(loop.get("topic") == "health_followup" for loop in state.open_loops))
        self.assertIn(state.current_arc, {"technical_progress", "health_followup"})

    def test_tc_phase3511_004_context_compiler_outputs_julia_context_v4(self):
        # TC-PHASE3511-004
        turn = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
            envelope(),
            "这个项目做了这么久还是感觉没完成。",
            user_intent={"mode": "emotional_support"},
        )
        context = turn.julia_context

        self.assertIsInstance(context.conversation_context, ConversationContinuityContext)
        self.assertEqual(context.conversation_context.current_arc, "project_pressure")
        self.assertIn("Project Pressure", context.conversation_context.active_topics)
        self.assertEqual(context.cognitive_mode.mode.name, "emotional_support")
        self.assertNotIn("provider", str(context.conversation_context).lower())
        self.assertNotIn("deepseek-chat", str(context.conversation_context).lower())

    def test_tc_phase3511_005_long_session_stability_caps_recent_turns_and_topics(self):
        # TC-PHASE3511-005
        manager = ContinuityManager(max_recent_turns=8, max_active_topics=5)
        state = None
        for index in range(1, 101):
            text = f"第{index}轮，继续 Julia Runtime 架构和调试。"
            topics = manager.topic_tracker.extract_topics(text)
            state = manager.update(state, ConversationTurn(index, text, "继续。", "2026-07-27", topics, "engineering_collaboration"))

        self.assertEqual(len(state.recent_turns), 8)
        self.assertLessEqual(len(state.active_topics), 5)
        self.assertEqual(state.current_arc, "technical_progress")
        self.assertIn("Julia Runtime", state.session_summary)


if __name__ == "__main__":
    unittest.main()
