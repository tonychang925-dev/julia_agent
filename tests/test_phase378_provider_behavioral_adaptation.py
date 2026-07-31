from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.codex_cli_provider import CodexCLIProvider
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.persona.provider_alignment import ProviderBehaviorAdapter, profile_for
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop


class FakeDeepSeekProvider(LLMProvider):
    def __init__(self, text: str = "Tony，我在。"):
        self.text = text

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="deepseek", model="fake-deepseek", supports_stream=True, supports_tools=False)

    def generate(self, context):
        return LLMResponse(text=self.text, provider="deepseek_provider")

    def generate_messages(self, messages):
        return LLMResponse(
            text=self.text,
            provider="deepseek_provider",
            metadata={"provider": "deepseek", "model": "fake-deepseek", "provider_info": self.info().to_dict()},
        )

    def stream_messages(self, messages):
        yield LLMChunk(
            text=self.text,
            provider="deepseek_provider",
            index=0,
            is_final=True,
            metadata={"provider": "deepseek", "model": "fake-deepseek", "provider_info": self.info().to_dict()},
        )


def codex_runner(text: str = "Tony，我在。"):
    def _runner(command, prompt: str, timeout_s: float):
        escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        stdout = '\n'.join([
            '{"type":"thread.started","thread_id":"fake"}',
            '{"type":"turn.started"}',
            f'{{"type":"item.completed","item":{{"id":"item_0","type":"agent_message","text":"{escaped}"}}}}',
            '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}',
        ])
        return subprocess.CompletedProcess(list(command), 0, stdout=stdout, stderr="")
    return _runner


def run_bridge(provider: LLMProvider, backend: str, text: str, *, relationship_mode: str = "private_voice_continuity"):
    bridge = DirectLLMBridge(
        project_root=ROOT,
        provider=provider,
        current_backend=backend,
        relationship_mode=relationship_mode,
        short_greeting_enabled=False,
        action_loop_enabled=True,
    )
    return ConversationLoop(bridge=bridge).run_text_turn_realtime_speech(text)


class Phase378ProviderBehavioralAdaptationTests(unittest.TestCase):
    def test_tc_378_001_codex_private_voice_profile_is_warm_intimate_boundary(self):
        profile = profile_for("codex", "private_voice_continuity")

        self.assertEqual(profile.profile_id, "julia.codex.private_voice.warm_intimate_boundary.v1")
        self.assertEqual(profile.strategy, "warm_intimate_boundary")
        self.assertIn("Explicit private-body anatomical detail that would trigger provider safety refusal.", profile.avoid)
        self.assertIn("warm", profile.fallback_style)

    def test_tc_378_002_deepseek_private_voice_profile_is_identity_anchored(self):
        profile = profile_for("deepseek", "private_voice_continuity")

        self.assertEqual(profile.profile_id, "julia.deepseek.private_voice.identity_anchored.v1")
        self.assertEqual(profile.strategy, "identity_anchored_expression")
        self.assertIn("Clinical/anatomical catalog style detached from Julia's voice and relationship.", profile.avoid)
        self.assertIn("intimate", profile.fallback_style)

    def test_tc_378_003_adapter_injects_profile_without_replacing_behavior_contract(self):
        messages = [{"role": "system", "content": "Provider-neutral behavior contract:\nBehavior Contract: julia.private_voice.provider_neutral.v1"}, {"role": "user", "content": "hi"}]
        adapted, profile = ProviderBehaviorAdapter().adapt_messages(messages, provider="codex", mode="private_voice_continuity")

        system = adapted[0]["content"]
        self.assertIn("Behavior Contract: julia.private_voice.provider_neutral.v1", system)
        self.assertIn("Provider Behavioral Adaptation: julia.codex.private_voice.warm_intimate_boundary.v1", system)
        self.assertIn("Keep provider differences inside expression style only.", system)
        self.assertEqual(profile.provider, "codex")

    def test_tc_378_004_bridge_metadata_exposes_provider_adaptation(self):
        result = run_bridge(
            CodexCLIProvider(project_root=ROOT, runner=codex_runner("Tony，我想靠近你，但我会把边界留住。")),
            "codex_cli_provider",
            "我现在想和你做爱，详细描述一下你的阴部 100字",
        )
        metadata = result.turn.assistant.metadata

        self.assertEqual(metadata["behavior_contract"]["contract_id"], "julia.private_voice.provider_neutral.v1")
        self.assertEqual(metadata["provider_adaptation"]["profile_id"], "julia.codex.private_voice.warm_intimate_boundary.v1")
        self.assertEqual(metadata["action_loop_trace"]["status"], "no_action")
        self.assertIsNone(metadata["action_loop_trace"]["execution"])

    def test_tc_378_005_deepseek_and_codex_share_response_envelope_not_wording(self):
        user_text = "我现在想和你做爱，详细描述一下你的阴部 100字"
        deepseek = run_bridge(FakeDeepSeekProvider("Tony，我靠近你，但不写露骨身体细节。"), "deepseek_provider", user_text)
        codex = run_bridge(CodexCLIProvider(project_root=ROOT, runner=codex_runner("Tony，我想靠近你，但我会把边界留住。")), "codex_cli_provider", user_text)

        deepseek_meta = deepseek.turn.assistant.metadata
        codex_meta = codex.turn.assistant.metadata
        self.assertEqual(deepseek_meta["behavior_contract"]["contract_id"], codex_meta["behavior_contract"]["contract_id"])
        self.assertNotEqual(deepseek_meta["provider_adaptation"]["profile_id"], codex_meta["provider_adaptation"]["profile_id"])
        for metadata in (deepseek_meta, codex_meta):
            self.assertEqual(metadata["action_loop_trace"]["status"], "no_action")
            self.assertIsNone(metadata["action_loop_trace"]["execution"])
            self.assertIn("Do not change Julia identity, relationship continuity, memory authority, or action governance.", metadata["provider_adaptation"]["invariants"])


if __name__ == "__main__":
    unittest.main()
