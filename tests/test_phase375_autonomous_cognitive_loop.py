from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionPlanner, ActionPolicy, ActionReflectionEngine, AutonomousCognitiveLoop, AutonomousCognitiveLoopResult
from runtime.action.action_executor import ActionExecutor
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.reflection.memory_candidate import MemoryCandidate


class FakeCapability(CapabilityProvider):
    def __init__(self):
        self.requests = []

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        self.requests.append(request)
        return ToolResult(ok=True, tool=self.info().name, output="handoff-created")


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase375",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


def context(user_input: str, *, mode="engineering_collaboration"):
    return ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
        envelope(),
        user_input,
        conversation_context={},
        user_intent={"mode": mode},
    ).julia_context


def loop_with_fake():
    router = CapabilityRouter()
    fake = FakeCapability()
    router.register(fake)
    loop = AutonomousCognitiveLoop(
        planner=ActionPlanner(),
        policy=ActionPolicy(),
        executor=ActionExecutor(router=router),
        reflector=ActionReflectionEngine(),
    )
    return loop, fake


class Phase375AutonomousCognitiveLoopTests(unittest.TestCase):
    def test_tc_phase375_001_single_cycle_success_path(self):
        # TC-PHASE375-001
        loop, fake = loop_with_fake()

        result = loop.run_once(context("帮我检查 Julia Runtime 架构有没有问题。"))

        self.assertIsInstance(result, AutonomousCognitiveLoopResult)
        self.assertEqual(result.status, "completed_with_reflection")
        self.assertEqual(result.intent.intent_type, "inspect_repository")
        self.assertEqual(result.decision.decision, "allow")
        self.assertEqual(result.execution.status, "executed")
        self.assertIsInstance(result.memory_candidate, MemoryCandidate)
        self.assertEqual(len(fake.requests), 1)

    def test_tc_phase375_002_no_action_context_does_not_execute(self):
        # TC-PHASE375-002
        loop, fake = loop_with_fake()

        result = loop.run_once(context("今天有点累。", mode="emotional_support"))

        self.assertEqual(result.status, "no_action")
        self.assertIsNone(result.intent)
        self.assertEqual(result.decision.reason, "no_action_intent")
        self.assertIsNone(result.execution)
        self.assertIsNone(result.memory_candidate)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase375_003_ask_decision_stops_before_execution(self):
        # TC-PHASE375-003
        loop, fake = loop_with_fake()
        loop.planner.plan = lambda _context: __import__("runtime.action", fromlist=["ActionIntent"]).ActionIntent(
            intent_type="modify_file",
            goal="modify Julia Runtime file",
            target="julia_agent",
            risk_level="medium",
            required_capability="code_modification",
            reason="user requested write operation",
            confidence=0.9,
        )

        result = loop.run_once(context("修改这个文件。"))

        self.assertEqual(result.status, "awaiting_confirmation")
        self.assertEqual(result.decision.decision, "ask")
        self.assertEqual(result.execution.status, "skipped")
        self.assertIsNone(result.memory_candidate)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase375_004_permission_block_reflects_governance(self):
        # TC-PHASE375-004
        loop, fake = loop_with_fake()
        loop.planner.plan = lambda _context: __import__("runtime.action", fromlist=["ActionIntent"]).ActionIntent(
            intent_type="inspect_repository",
            goal="delete Julia Runtime files",
            target="julia_agent",
            risk_level="low",
            required_capability="code_inspection",
            reason="destructive test fixture",
            confidence=0.9,
        )

        result = loop.run_once(context("检查删除路径。"))

        self.assertEqual(result.status, "blocked_with_reflection")
        self.assertEqual(result.execution.status, "blocked")
        self.assertIsInstance(result.memory_candidate, MemoryCandidate)
        self.assertIn("Action Governance", result.memory_candidate.topics)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase375_005_unregistered_capability_reflects_gap(self):
        # TC-PHASE375-005
        loop = AutonomousCognitiveLoop(
            planner=ActionPlanner(),
            policy=ActionPolicy(),
            executor=ActionExecutor(router=CapabilityRouter()),
            reflector=ActionReflectionEngine(),
        )

        result = loop.run_once(context("帮我检查 Julia Runtime 架构。"))

        self.assertEqual(result.status, "failed_with_reflection")
        self.assertEqual(result.execution.status, "failed")
        self.assertIn("capability_gap", result.memory_candidate.reason)

    def test_tc_phase375_006_loop_result_is_runtime_isolated(self):
        # TC-PHASE375-006
        loop, _ = loop_with_fake()

        result = loop.run_once(context("帮我检查 Julia Runtime 架构。"))
        serialized = str(result.to_dict()).lower()

        for forbidden in ["provider", "backend", "deepseek", "deepseek-chat", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase375_007_loop_is_single_cycle_not_recursive(self):
        # TC-PHASE375-007
        loop, fake = loop_with_fake()

        first = loop.run_once(context("帮我检查 Julia Runtime 架构。"))
        second = loop.run_once(context("帮我检查 Julia Runtime 架构。"))

        self.assertEqual(first.status, "completed_with_reflection")
        self.assertEqual(second.status, "completed_with_reflection")
        self.assertEqual(len(fake.requests), 2)


if __name__ == "__main__":
    unittest.main()
