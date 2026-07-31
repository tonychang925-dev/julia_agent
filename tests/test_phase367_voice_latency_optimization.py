from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class Phase367VoiceLatencyOptimizationTests(unittest.TestCase):
    def test_tc_phase367_001_voice_latency_policy_adds_voice_only_constraints(self):
        from runtime.conversation_runtime.voice_latency_policy import VoiceLatencyPolicy

        messages = [
            {"role": "system", "content": "Identity\nSelected memory: keep"},
            {"role": "user", "content": "今天有点累。"},
        ]
        metadata = {}
        optimized = VoiceLatencyPolicy(enabled=True, max_tokens=160, first_sentence_chars=24, max_sentences=8).apply(messages, metadata)

        self.assertIn("Voice latency policy", optimized[0]["content"])
        self.assertIn("spoken first sentence", optimized[0]["content"])
        self.assertIn("Selected memory: keep", optimized[0]["content"])
        self.assertEqual(metadata["voice_latency_policy"]["enabled"], True)
        self.assertEqual(metadata["voice_latency_policy"]["max_tokens"], 160)
        self.assertEqual(metadata["voice_latency_policy"]["first_sentence_chars"], 24)
        self.assertEqual(metadata["voice_latency_policy"]["max_sentences"], 8)

    def test_tc_phase367_002_voice_latency_policy_can_be_disabled(self):
        from runtime.conversation_runtime.voice_latency_policy import VoiceLatencyPolicy

        messages = [{"role": "system", "content": "Identity"}, {"role": "user", "content": "Julia，在吗？"}]
        metadata = {}
        optimized = VoiceLatencyPolicy(enabled=False).apply(messages, metadata)

        self.assertEqual(optimized, messages)
        self.assertNotIn("voice_latency_policy", metadata)

    def test_tc_phase367_003_deepseek_provider_passes_max_tokens_to_client_payload(self):
        from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider

        class CaptureClient:
            def __init__(self):
                self.messages = None
                self.kwargs = None

            def stream_chat(self, messages, **kwargs):
                self.messages = messages
                self.kwargs = kwargs
                yield type("Chunk", (), {
                    "text": "嗯。",
                    "index": 0,
                    "is_final": False,
                    "model": "fake",
                    "latency_ms": 1,
                    "timings": {},
                    "raw": {},
                })()
                yield type("Chunk", (), {
                    "text": "",
                    "index": 1,
                    "is_final": True,
                    "model": "fake",
                    "latency_ms": 2,
                    "timings": {},
                    "raw": {},
                })()

        client = CaptureClient()
        provider = DeepSeekProvider(api_key="test", client=client, max_tokens=88, temperature=0.3)
        list(provider.stream_messages([{"role": "user", "content": "hi"}]))

        self.assertEqual(client.kwargs["max_tokens"], 88)
        self.assertEqual(client.kwargs["temperature"], 0.3)

    def test_tc_phase367_004_direct_bridge_marks_voice_latency_policy_metadata(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
        from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider
        from runtime.cognitive.provider.openai_compatible import OpenAICompatibleChunk

        class FakeClient:
            def __init__(self):
                self.messages = None
                self.kwargs = None

            def stream_chat(self, messages, **kwargs):
                self.messages = messages
                self.kwargs = kwargs
                yield OpenAICompatibleChunk(text="嗯。", index=0, model="fake", latency_ms=10, timings={})
                yield OpenAICompatibleChunk(text="", index=1, model="fake", is_final=True, latency_ms=10, timings={})

        provider = DeepSeekProvider(api_key="test", client=FakeClient(), max_tokens=320)
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="deepseek_provider", voice_latency_optimized=True)
        bridge.send_message("今天有点累。", session_id="s", turn_id=1)
        chunks = list(bridge.stream_response(session_id="s", turn_id=1))

        self.assertTrue(chunks[0].metadata["voice_latency_policy"]["enabled"])
        self.assertIn("Voice latency policy", provider.client.messages[0]["content"])

    def test_tc_phase367_005_deepseek_factory_enables_voice_latency_policy(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge

        bridge = DirectLLMBridge.deepseek(
            ROOT,
            api_key="",
            voice_latency_optimized=True,
            voice_max_tokens=96,
        )

        self.assertTrue(bridge.voice_latency_optimized)
        self.assertEqual(bridge.voice_max_tokens, 96)
        self.assertEqual(bridge.provider.max_tokens, 96)
        self.assertEqual(bridge.provider.temperature, 0.5)

    def test_tc_phase367_006_default_voice_budget_is_320_tokens(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge

        bridge = DirectLLMBridge.deepseek(ROOT, api_key="", voice_latency_optimized=True)

        self.assertEqual(bridge.voice_max_tokens, 320)
        self.assertEqual(bridge.provider.max_tokens, 320)

    def test_tc_phase367_007_tts_hard_split_prefers_clause_boundary_over_enumeration_mark(self):
        from tts.chunking import split_for_tts

        text = "先把 Persona Package 的接口定义写清楚，然后我就能在 Claude、GPT 和 DeepSeek 之间自由迁移了。"
        chunks = split_for_tts(text, max_chars=60)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertFalse(chunks[0].endswith("Claude、"))
        self.assertTrue(chunks[0].endswith("清楚，"), chunks)

    def test_tc_phase367_008_voice_policy_requires_core_object_preservation(self):
        from runtime.conversation_runtime.voice_latency_policy import VoiceLatencyPolicy

        messages = [{"role": "system", "content": "Identity"}, {"role": "user", "content": "我们现在在忙什么。"}]
        metadata = {}
        optimized = VoiceLatencyPolicy(enabled=True).apply(messages, metadata)

        content = optimized[0]["content"]
        self.assertIn("Preserve core objects", content)
        self.assertIn("Julia Runtime", content)
        self.assertIn("do not replace", content)
        self.assertIn("你的系统", content)

    def test_tc_phase367_009_voice_policy_exposes_semantic_guard_metadata(self):
        from runtime.conversation_runtime.voice_latency_policy import VoiceLatencyPolicy

        metadata = {}
        VoiceLatencyPolicy(enabled=True).apply([{"role": "system", "content": "Identity"}], metadata)

        guard = metadata["voice_latency_policy"]["semantic_guard"]
        self.assertEqual(guard["scope"], "core_object_preservation")
        self.assertIn("Julia Runtime", guard["protected_terms"])


if __name__ == "__main__":
    unittest.main()
