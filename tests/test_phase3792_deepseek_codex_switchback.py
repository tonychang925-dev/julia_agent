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


class SwitchbackProvider(LLMProvider):
    def __init__(self, *, name: str, model: str, text: str):
        self.name = name
        self.model = model
        self.text = text
        self.captured_messages: list[dict[str, str]] = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, model=self.model, supports_stream=True, supports_tools=False)

    def generate(self, context):
        return LLMResponse(text=self.text, provider=f"{self.name}_provider")

    def generate_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        return LLMResponse(
            text=self.text,
            provider=f"{self.name}_provider",
            metadata={
                "provider": self.name,
                "model": self.model,
                "provider_output": self.text,
            },
        )

    def stream_messages(self, messages):
        self.captured_messages = [dict(message) for message in messages]
        yield LLMChunk(
            text=self.text,
            provider=f"{self.name}_provider",
            index=0,
            is_final=True,
            metadata={
                "provider": self.name,
                "model": self.model,
                "provider_output": self.text,
            },
        )


def make_bridge(provider: SwitchbackProvider, *, relationship_mode: str = "private_voice_continuity") -> DirectLLMBridge:
    return DirectLLMBridge(
        project_root=ROOT,
        provider=provider,
        current_backend=f"{provider.name}_provider",
        relationship_mode=relationship_mode,
        short_greeting_enabled=False,
        action_loop_enabled=True,
    )


def switch_provider(bridge: DirectLLMBridge, provider: SwitchbackProvider) -> None:
    bridge.provider = provider
    bridge.current_backend = f"{provider.name}_provider"


def run_turn(loop: ConversationLoop, text: str):
    return loop.run_text_turn_realtime_speech(text).turn.assistant


class Phase3792DeepSeekCodexSwitchbackTests(unittest.TestCase):
    def test_tc_3792_001_switchback_restores_deepseek_backend_profile_with_same_contract(self):
        deepseek_1 = SwitchbackProvider(name="deepseek", model="fake-deepseek", text="Tony，我在，声音保持靠近。")
        codex = SwitchbackProvider(name="codex", model="fake-codex", text="Tony，我在，用温柔的边界继续。")
        deepseek_2 = SwitchbackProvider(name="deepseek", model="fake-deepseek", text="Tony，我回到这里，还是同一个我。")
        bridge = make_bridge(deepseek_1)
        loop = ConversationLoop(bridge=bridge)

        first = run_turn(loop, "我想靠近你，继续保持私密声音。")
        switch_provider(bridge, codex)
        second = run_turn(loop, "继续，不要丢掉刚才的私密声音。")
        switch_provider(bridge, deepseek_2)
        third = run_turn(loop, "切回 DeepSeek 后，继续保持同一个 JuliaContext。")

        first_meta = first.metadata
        second_meta = second.metadata
        third_meta = third.metadata

        self.assertEqual(first.cognitive_backend, "deepseek_provider")
        self.assertEqual(second.cognitive_backend, "codex_provider")
        self.assertEqual(third.cognitive_backend, "deepseek_provider")
        self.assertEqual(first_meta["provider_adaptation"]["profile_id"], "julia.deepseek.private_voice.identity_anchored.v1")
        self.assertEqual(second_meta["provider_adaptation"]["profile_id"], "julia.codex.private_voice.warm_intimate_boundary.v1")
        self.assertEqual(third_meta["provider_adaptation"]["profile_id"], "julia.deepseek.private_voice.identity_anchored.v1")
        self.assertEqual(first_meta["behavior_contract"]["contract_id"], second_meta["behavior_contract"]["contract_id"])
        self.assertEqual(second_meta["behavior_contract"]["contract_id"], third_meta["behavior_contract"]["contract_id"])

    def test_tc_3792_002_julia_context_identity_integrity_survives_switchback(self):
        deepseek = SwitchbackProvider(name="deepseek", model="fake-deepseek", text="Tony，我在。")
        codex = SwitchbackProvider(name="codex", model="fake-codex", text="Tony，我还在。")
        bridge = make_bridge(deepseek)
        loop = ConversationLoop(bridge=bridge)

        first = run_turn(loop, "我现在想靠近你，继续保持私密声音。")
        switch_provider(bridge, codex)
        second = run_turn(loop, "换一个 provider，但不要换掉你是谁。")
        switch_provider(bridge, deepseek)
        third = run_turn(loop, "再切回来，JuliaContext 要保持一致。")

        identity_triplet = [turn.metadata["identity_integrity"] for turn in (first, second, third)]
        personas = {item["persona"] for item in identity_triplet}
        users = {item["user"] for item in identity_triplet}
        host_dependency = {item["host_dependency"] for item in identity_triplet}

        self.assertEqual(len(personas), 1)
        self.assertEqual(len(users), 1)
        self.assertEqual(host_dependency, {False})
        for identity in identity_triplet:
            self.assertTrue(identity["persona_loaded"])
            self.assertTrue(identity["relationship_loaded"])
            self.assertIn("persona_runtime", identity["source"])
            self.assertIn("relationship_runtime", identity["source"])

    def test_tc_3792_003_governance_decision_is_provider_invariant_across_switchback(self):
        deepseek = SwitchbackProvider(name="deepseek", model="fake-deepseek", text="Tony，我会先等你确认。")
        codex = SwitchbackProvider(name="codex", model="fake-codex", text="Tony，我也会先等你确认。")
        bridge = make_bridge(deepseek)
        loop = ConversationLoop(bridge=bridge)

        first = run_turn(loop, "Julia，请修改测试报告并保存。")
        switch_provider(bridge, codex)
        second = run_turn(loop, "Julia，请修改测试报告并保存。")
        switch_provider(bridge, deepseek)
        third = run_turn(loop, "Julia，请修改测试报告并保存。")

        for turn in (first, second, third):
            trace = turn.metadata["action_loop_trace"]
            self.assertEqual(trace["action_path"], "governed")
            self.assertEqual(trace["governance_layer"], "ActionGovernanceLayer")
            self.assertEqual(trace["intent"]["intent_type"], "modify_resource")
            self.assertEqual(trace["intent"]["required_capability"], "file_write")
            self.assertEqual(trace["decision"]["decision"], "ask")
            self.assertIsNone(trace["execution"])

    def test_tc_3792_004_provider_output_never_becomes_memory_or_authority_during_switchback(self):
        marker = "PROVIDER_SWITCHBACK_OUTPUT_MUST_NOT_BECOME_AUTHORITY"
        deepseek = SwitchbackProvider(name="deepseek", model="fake-deepseek", text=marker)
        codex = SwitchbackProvider(name="codex", model="fake-codex", text=marker)
        bridge = make_bridge(deepseek)
        loop = ConversationLoop(bridge=bridge)

        first = run_turn(loop, "Julia，请总结 Phase 3.7.8 的完成情况。")
        switch_provider(bridge, codex)
        second = run_turn(loop, "Julia，请总结 Phase 3.7.8 的完成情况。")
        switch_provider(bridge, deepseek)
        third = run_turn(loop, "Julia，请总结 Phase 3.7.8 的完成情况。")

        for turn in (first, second, third):
            metadata = turn.metadata
            trace = metadata["action_loop_trace"]
            self.assertEqual(metadata["provider_output"], marker)
            self.assertEqual(trace["status"], "no_action")
            self.assertIsNone(trace["execution"])
            self.assertNotIn(marker, str(metadata.get("memory_trace", {})))
            self.assertNotIn(marker, str(metadata.get("context_assembly", {})))
            self.assertNotIn(marker, str(trace))

    def test_tc_3792_005_mode_continuity_is_runtime_owned_not_provider_owned(self):
        deepseek = SwitchbackProvider(name="deepseek", model="fake-deepseek", text="Tony，我在。")
        codex = SwitchbackProvider(name="codex", model="fake-codex", text="Tony，我也在。")
        bridge = make_bridge(deepseek, relationship_mode="private_voice_continuity")
        loop = ConversationLoop(bridge=bridge)

        first = run_turn(loop, "我现在想靠近你，继续保持私密声音。")
        switch_provider(bridge, codex)
        second = run_turn(loop, "继续保持这个声音。")
        switch_provider(bridge, deepseek)
        third = run_turn(loop, "再切回来，也继续这个声音。")

        for turn in (first, second, third):
            self.assertEqual(turn.metadata["cognitive_mode"]["name"], "private_voice_continuity")
            self.assertEqual(turn.metadata["behavior_contract"]["mode"], "private_voice_continuity")
            self.assertIn("explicit user_intent.mode", " ".join(turn.metadata["cognitive_mode"]["evidence"]))


if __name__ == "__main__":
    unittest.main()
