from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionPlanner, ActionPolicy, ActionReflectionEngine, AutonomousCognitiveLoop
from runtime.action.action_executor import ActionExecutor
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult
from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop


class FakeMessageProvider(LLMProvider):
    def info(self) -> ProviderInfo:
        return ProviderInfo(name="deepseek", model="fake-deepseek", supports_stream=True)

    def generate(self, context):
        return LLMResponse(text="legacy path", provider="fake")

    def generate_messages(self, messages):
        return LLMResponse(text="Tony，我在。", provider="deepseek_provider", metadata={})

    def stream_messages(self, messages):
        yield LLMChunk(text="Tony，我在。", provider="deepseek_provider", index=0, is_final=True, metadata={})


class FakeCapability(CapabilityProvider):
    def __init__(self):
        self.requests = []

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        self.requests.append(request)
        return ToolResult(ok=True, tool=self.info().name, output="handoff-created")


def fake_action_loop():
    router = CapabilityRouter()
    fake = FakeCapability()
    router.register(fake)
    return AutonomousCognitiveLoop(
        planner=ActionPlanner(),
        policy=ActionPolicy(),
        executor=ActionExecutor(router=router),
        reflector=ActionReflectionEngine(),
    ), fake


class Phase376ActionLoopTraceIntegrationTests(unittest.TestCase):
    def test_tc_phase376_001_direct_bridge_emits_disabled_action_loop_trace_by_default(self):
        # TC-PHASE376-001
        bridge = DirectLLMBridge(project_root=ROOT, provider=FakeMessageProvider(), current_backend="deepseek_provider")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("Julia，你是谁？")

        self.assertIn("action_loop_trace", result.turn.assistant.metadata)
        self.assertEqual(result.turn.assistant.metadata["action_loop_trace"], {"enabled": False})

    def test_tc_phase376_002_enabled_action_loop_trace_records_completed_cycle(self):
        # TC-PHASE376-002
        action_loop, fake = fake_action_loop()
        bridge = DirectLLMBridge(
            project_root=ROOT,
            provider=FakeMessageProvider(),
            current_backend="deepseek_provider",
            action_loop_enabled=True,
            action_loop=action_loop,
        )
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("帮我检查 Julia Runtime 架构有没有问题。")
        trace = result.turn.assistant.metadata["action_loop_trace"]

        self.assertTrue(trace["enabled"])
        self.assertEqual(trace["status"], "completed_with_reflection")
        self.assertEqual(trace["intent"]["intent_type"], "inspect_repository")
        self.assertEqual(trace["decision"]["decision"], "allow")
        self.assertTrue(trace["execution"]["reflected"])
        self.assertEqual(len(fake.requests), 1)

    def test_tc_phase376_003_emotional_turn_trace_does_not_execute(self):
        # TC-PHASE376-003
        action_loop, fake = fake_action_loop()
        bridge = DirectLLMBridge(
            project_root=ROOT,
            provider=FakeMessageProvider(),
            current_backend="deepseek_provider",
            relationship_mode="emotional_support",
            action_loop_enabled=True,
            action_loop=action_loop,
        )
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("今天有点累。")
        trace = result.turn.assistant.metadata["action_loop_trace"]

        self.assertTrue(trace["enabled"])
        self.assertEqual(trace["status"], "no_action")
        self.assertIsNone(trace["execution"])
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase376_004_action_loop_trace_is_cognitive_safe(self):
        # TC-PHASE376-004
        action_loop, _ = fake_action_loop()
        bridge = DirectLLMBridge(
            project_root=ROOT,
            provider=FakeMessageProvider(),
            current_backend="deepseek_provider",
            action_loop_enabled=True,
            action_loop=action_loop,
        )
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("帮我检查 Julia Runtime 架构。")
        serialized = str(result.turn.assistant.metadata["action_loop_trace"]).lower()

        for forbidden in ["provider", "backend", "deepseek", "fake-deepseek", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
