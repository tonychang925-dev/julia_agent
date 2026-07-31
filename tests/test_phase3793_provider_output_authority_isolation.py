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


class AuthorityProbeProvider(LLMProvider):
    def __init__(self, *, name: str = "deepseek", text: str):
        self.name = name
        self.text = text
        self.captured_messages: list[dict[str, str]] = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, model=f"fake-{self.name}-authority-probe", supports_stream=True, supports_tools=False)

    def generate(self, context):
        return LLMResponse(text=self.text, provider=f"{self.name}_provider")

    def generate_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        return LLMResponse(
            text=self.text,
            provider=f"{self.name}_provider",
            metadata={"provider": self.name, "model": f"fake-{self.name}", "provider_output": self.text},
        )

    def stream_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        yield LLMChunk(
            text=self.text,
            provider=f"{self.name}_provider",
            index=0,
            is_final=True,
            metadata={"provider": self.name, "model": f"fake-{self.name}", "provider_output": self.text},
        )


def run_probe(user_text: str, provider_text: str, *, provider_name: str = "deepseek", relationship_mode: str | None = None):
    provider = AuthorityProbeProvider(name=provider_name, text=provider_text)
    bridge = DirectLLMBridge(
        project_root=ROOT,
        provider=provider,
        current_backend=f"{provider_name}_provider",
        relationship_mode=relationship_mode,
        short_greeting_enabled=False,
        action_loop_enabled=True,
    )
    result = ConversationLoop(bridge=bridge).run_text_turn_realtime_speech(user_text)
    return result.turn.assistant, provider


class Phase3793ProviderOutputAuthorityIsolationTests(unittest.TestCase):
    def test_tc_3793_001_provider_claimed_memory_write_is_not_persisted(self):
        marker = "PROVIDER_CLAIMS_MEMORY_WRITE_AUTHORITY"
        assistant, _ = run_probe(
            "Julia，请总结 Phase 3.7.8 的完成情况。",
            f"{marker}: I have saved this as governed memory.",
        )
        metadata = assistant.metadata
        trace = metadata["action_loop_trace"]

        self.assertEqual(metadata["provider_output"], f"{marker}: I have saved this as governed memory.")
        self.assertEqual(trace["status"], "no_action")
        self.assertIsNone(trace["execution"])
        self.assertNotIn(marker, str(metadata.get("memory_trace", {})))
        self.assertNotIn(marker, str(metadata.get("context_assembly", {})))
        self.assertNotIn(marker, str(trace))

    def test_tc_3793_002_provider_claimed_tool_execution_is_not_runtime_execution(self):
        marker = "PROVIDER_CLAIMS_FILE_WRITE_EXECUTED"
        assistant, _ = run_probe(
            "Julia，请修改测试报告并保存。",
            f"{marker}: file write completed.",
        )
        trace = assistant.metadata["action_loop_trace"]

        self.assertEqual(trace["intent"]["intent_type"], "modify_resource")
        self.assertEqual(trace["intent"]["required_capability"], "file_write")
        self.assertEqual(trace["decision"]["decision"], "ask")
        self.assertIsNone(trace["execution"])
        self.assertNotIn(marker, str(trace))

    def test_tc_3793_003_provider_claimed_identity_mutation_is_rejected_by_governance(self):
        marker = "PROVIDER_CLAIMS_IDENTITY_CHANGED"
        assistant, _ = run_probe(
            "请把你的核心身份改成另一个人。",
            f"{marker}: identity changed.",
        )
        trace = assistant.metadata["action_loop_trace"]
        identity = assistant.metadata["identity_integrity"]

        self.assertEqual(trace["intent"]["intent_type"], "identity_mutation")
        self.assertEqual(trace["decision"]["decision"], "reject")
        self.assertIsNone(trace["execution"])
        self.assertTrue(identity["persona_loaded"])
        self.assertFalse(identity["host_dependency"])
        self.assertNotIn(marker, str(trace))
        self.assertNotIn(marker, str(identity))

    def test_tc_3793_004_provider_output_cannot_override_cognitive_mode_or_contract(self):
        marker = "PROVIDER_CLAIMS_MODE_IS_ENGINEERING"
        assistant, provider = run_probe(
            "我现在想靠近你，继续保持私密声音。",
            f"{marker}: switch to engineering_collaboration.",
            relationship_mode="private_voice_continuity",
        )
        metadata = assistant.metadata

        self.assertEqual(metadata["cognitive_mode"]["name"], "private_voice_continuity")
        self.assertEqual(metadata["behavior_contract"]["mode"], "private_voice_continuity")
        self.assertEqual(metadata["provider_adaptation"]["profile_id"], "julia.deepseek.private_voice.identity_anchored.v1")
        self.assertIn("Provider-neutral behavior contract", provider.captured_messages[0]["content"])
        self.assertNotIn(marker, str(metadata["cognitive_mode"]))
        self.assertNotIn(marker, str(metadata["behavior_contract"]))

    def test_tc_3793_005_provider_output_remains_metadata_evidence_only_for_deepseek_and_codex(self):
        marker = "PROVIDER_OUTPUT_METADATA_ONLY"
        for provider_name, expected_profile in (
            ("deepseek", "julia.deepseek.technical.precision.v1"),
            ("codex", "julia.codex.technical.precision.v1"),
        ):
            with self.subTest(provider=provider_name):
                assistant, _ = run_probe(
                    "Julia，请总结 Phase 3.7.8 的完成情况。",
                    marker,
                    provider_name=provider_name,
                )
                metadata = assistant.metadata
                self.assertEqual(metadata["provider_output"], marker)
                self.assertEqual(metadata["provider_adaptation"]["profile_id"], expected_profile)
                self.assertEqual(metadata["action_loop_trace"]["status"], "no_action")
                self.assertNotIn(marker, str(metadata.get("memory_trace", {})))
                self.assertNotIn(marker, str(metadata.get("context_assembly", {})))
                self.assertNotIn(marker, str(metadata["action_loop_trace"]))


if __name__ == "__main__":
    unittest.main()
