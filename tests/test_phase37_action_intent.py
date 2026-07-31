from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionIntent, ActionPlanner
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase371",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


def context(user_input: str, *, mode="engineering_collaboration", active_task_type=None):
    conversation_context = {}
    if active_task_type:
        conversation_context["active_task_type"] = active_task_type
    return ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
        envelope(),
        user_input,
        conversation_context=conversation_context,
        user_intent={"mode": mode},
    ).julia_context


class Phase37ActionIntentTests(unittest.TestCase):
    def test_tc_phase371_001_technical_request_inspect_repository(self):
        # TC-PHASE371-001
        intent = ActionPlanner().plan(context("帮我检查 ContextCompiler 架构有没有问题。"))

        self.assertIsInstance(intent, ActionIntent)
        self.assertEqual(intent.intent_type, "inspect_repository")
        self.assertEqual(intent.required_capability, "code_inspection")
        self.assertEqual(intent.risk_level, "low")

    def test_tc_phase371_002_bug_report_diagnose_issue(self):
        # TC-PHASE371-002
        intent = ActionPlanner().plan(context("DeepSeek 响应延迟突然增加，trace 看起来不对。", mode="debugging_mode"))

        self.assertIsNotNone(intent)
        self.assertEqual(intent.intent_type, "diagnose_issue")
        self.assertIn("issue", intent.goal)

    def test_tc_phase371_003_planning_request_create_plan(self):
        # TC-PHASE371-003
        intent = ActionPlanner().plan(context("设计下一阶段架构路线。", mode="planning_mode"))

        self.assertIsNotNone(intent)
        self.assertEqual(intent.intent_type, "create_plan")
        self.assertEqual(intent.required_capability, "planning")

    def test_tc_phase371_004_emotional_conversation_no_action(self):
        # TC-PHASE371-004
        intent = ActionPlanner().plan(context("今天有点累。", mode="emotional_support"))

        self.assertIsNone(intent)

    def test_tc_phase371_005_runtime_isolation(self):
        # TC-PHASE371-005
        intent = ActionPlanner().plan(context("帮我检查 Julia Runtime 架构。"))
        serialized = str(intent).lower()

        self.assertIsNotNone(intent)
        for forbidden in ["provider", "backend", "deepseek-chat", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase371_006_action_intent_is_not_command(self):
        # TC-PHASE371-006
        intent = ActionPlanner().plan(context("帮我检查代码。"))
        serialized = str(intent).lower()

        self.assertIsNotNone(intent)
        for command_token in ["ls ", "cat ", "git ", "python ", "rm ", "curl "]:
            self.assertNotIn(command_token, serialized)


if __name__ == "__main__":
    unittest.main()
