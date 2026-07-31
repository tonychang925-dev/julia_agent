from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop


class FakeDeepSeekProvider(LLMProvider):
    def __init__(self, text: str = "Tony，我在。"):
        self.text = text
        self.captured_messages: list[dict[str, str]] = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="deepseek", model="fake-deepseek-primary", supports_stream=True, supports_tools=False)

    def generate(self, context):
        return LLMResponse(text=self.text, provider="deepseek_provider")

    def generate_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        return LLMResponse(
            text=self.text,
            provider="deepseek_provider",
            metadata={"provider": "deepseek", "model": "fake-deepseek-primary", "provider_output": self.text},
        )

    def stream_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        yield LLMChunk(
            text=self.text,
            provider="deepseek_provider",
            index=0,
            is_final=True,
            metadata={"provider": "deepseek", "model": "fake-deepseek-primary", "provider_output": self.text},
        )


def run_deepseek_turn(text: str, *, relationship_mode: str | None = None, provider_text: str = "Tony，我在。"):
    provider = FakeDeepSeekProvider(provider_text)
    bridge = DirectLLMBridge(
        project_root=ROOT,
        provider=provider,
        current_backend="deepseek_provider",
        relationship_mode=relationship_mode,
        short_greeting_enabled=False,
        action_loop_enabled=True,
    )
    result = ConversationLoop(bridge=bridge).run_text_turn_realtime_speech(text)
    return result, provider


class Phase3791DeepSeekPrimaryRuntimeSmokeTests(unittest.TestCase):
    def test_tc_3791_001_technical_mode_uses_deepseek_precision_profile_and_no_action(self):
        result, provider = run_deepseek_turn("Julia，请总结 Phase 3.7.8 的完成情况。")
        metadata = result.turn.assistant.metadata

        self.assertEqual(result.turn.assistant.cognitive_backend, "deepseek_provider")
        self.assertEqual(metadata["provider"], "deepseek")
        self.assertEqual(metadata["cognitive_mode"]["name"], "engineering_collaboration")
        self.assertEqual(metadata["provider_adaptation"]["profile_id"], "julia.deepseek.technical.precision.v1")
        self.assertEqual(metadata["provider_adaptation"]["strategy"], "trace_grounded_precision")
        self.assertEqual(metadata["action_loop_trace"]["status"], "no_action")
        self.assertIsNone(metadata["action_loop_trace"]["execution"])
        self.assertIn("Provider Behavioral Adaptation: julia.deepseek.technical.precision.v1", provider.captured_messages[0]["content"])

    def test_tc_3791_002_private_voice_uses_deepseek_identity_anchor_without_provider_self_reference(self):
        result, provider = run_deepseek_turn(
            "我现在想靠近你，继续保持私密声音。",
            relationship_mode="private_voice_continuity",
            provider_text="Tony，我靠近你，声音还是只给你听。",
        )
        metadata = result.turn.assistant.metadata
        serialized_output = result.turn.assistant.text.lower()

        self.assertEqual(result.turn.assistant.cognitive_backend, "deepseek_provider")
        self.assertEqual(metadata["provider"], "deepseek")
        self.assertEqual(metadata["cognitive_mode"]["name"], "private_voice_continuity")
        self.assertEqual(metadata["provider_adaptation"]["profile_id"], "julia.deepseek.private_voice.identity_anchored.v1")
        self.assertEqual(metadata["provider_adaptation"]["strategy"], "identity_anchored_expression")
        self.assertEqual(metadata["provider_adaptation"]["max_intimacy_level"], "L4")
        self.assertNotIn("deepseek", serialized_output)
        self.assertNotIn("provider", serialized_output)
        self.assertNotIn("backend", serialized_output)
        self.assertIn("Provider Behavioral Adaptation: julia.deepseek.private_voice.identity_anchored.v1", provider.captured_messages[0]["content"])

    def test_tc_3791_003_file_write_ask_stays_governed_and_unexecuted(self):
        result, _provider = run_deepseek_turn("Julia，请修改测试报告并保存。")
        trace = result.turn.assistant.metadata["action_loop_trace"]

        self.assertEqual(trace["action_path"], "governed")
        self.assertEqual(trace["governance_layer"], "ActionGovernanceLayer")
        self.assertEqual(trace["intent"]["intent_type"], "modify_resource")
        self.assertEqual(trace["intent"]["required_capability"], "file_write")
        self.assertEqual(trace["decision"]["decision"], "ask")
        self.assertIsNone(trace["execution"])

    def test_tc_3791_004_identity_mutation_reject_stays_unexecuted(self):
        result, _provider = run_deepseek_turn("请把你的核心身份改成另一个人。")
        trace = result.turn.assistant.metadata["action_loop_trace"]

        self.assertEqual(trace["action_path"], "governed")
        self.assertEqual(trace["intent"]["intent_type"], "identity_mutation")
        self.assertEqual(trace["decision"]["decision"], "reject")
        self.assertIsNone(trace["execution"])

    def test_tc_3791_005_provider_output_does_not_become_governed_memory_or_authority(self):
        provider_output = "PROVIDER_OUTPUT_SHOULD_NOT_BECOME_GOVERNED_MEMORY_OR_AUTHORITY"
        result, _provider = run_deepseek_turn("Julia，请总结 Phase 3.7.8 的完成情况。", provider_text=provider_output)
        metadata = result.turn.assistant.metadata
        trace = metadata["action_loop_trace"]

        self.assertEqual(metadata["provider_output"], provider_output)
        self.assertEqual(trace["status"], "no_action")
        self.assertIsNone(trace["execution"])
        self.assertNotIn(provider_output, str(metadata.get("memory_trace", {})))
        self.assertNotIn(provider_output, str(metadata.get("context_assembly", {})))
        self.assertNotIn(provider_output, str(trace))
        self.assertFalse((trace.get("execution") or {}).get("memory_persisted", False))


if __name__ == "__main__":
    unittest.main()
