from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_builder import ContextBuilder
from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider
from runtime.cognitive.provider.openai_compatible import OpenAICompatibleChunk, OpenAICompatibleResult
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState


class FakeOpenAICompatibleClient:
    def __init__(self):
        self.last_messages = None

    def chat(self, messages):
        self.last_messages = messages
        return OpenAICompatibleResult(
            text="我是Julia，Tony。我由 Julia Runtime 的上下文驱动，并通过 DeepSeekProvider 思考。",
            model="deepseek-chat-test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            latency_ms=12,
        )

    def stream_chat(self, messages):
        self.last_messages = messages
        yield OpenAICompatibleChunk(text="我是Julia，Tony。", index=0, is_final=False, model="deepseek-chat-test", latency_ms=5)
        yield OpenAICompatibleChunk(text="我通过 DirectLLMBridge 思考。", index=1, is_final=True, model="deepseek-chat-test", latency_ms=15)


class Phase33DeepSeekProviderTests(unittest.TestCase):
    def test_tc_phase33_008_deepseek_provider_contract_uses_julia_context(self):
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_deepseek_contract", current_backend="deepseek_provider")
        fake = FakeOpenAICompatibleClient()
        provider = DeepSeekProvider(api_key="test-key", client=fake)

        response = provider.generate(context)

        self.assertTrue(response.ok)
        self.assertEqual(response.provider, "deepseek_provider")
        self.assertIn("Julia", response.text)
        self.assertIn("Tony", response.text)
        self.assertEqual(response.metadata["provider"], "deepseek")
        self.assertEqual(response.metadata["model"], "deepseek-chat-test")
        self.assertEqual(response.metadata["usage"]["total_tokens"], 30)
        self.assertEqual(response.metadata["context_runtime_state"]["current_backend"], "deepseek_provider")
        self.assertIn("provider_timing", response.metadata)
        self.assertIn("prompt_build_ms", response.metadata["provider_timing"])
        self.assertIn("prompt_input_chars", response.metadata["provider_timing"])
        self.assertIsNotNone(fake.last_messages)
        self.assertEqual(fake.last_messages[0]["role"], "system")
        self.assertEqual(fake.last_messages[-1]["content"], "Julia，你是谁？")

    def test_tc_phase33_009_deepseek_provider_stream_contract_emits_llm_chunks(self):
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_deepseek_stream", current_backend="deepseek_provider")
        provider = DeepSeekProvider(api_key="test-key", client=FakeOpenAICompatibleClient())

        chunks = list(provider.stream(context))

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].provider, "deepseek_provider")
        self.assertEqual(chunks[0].text, "我是Julia，Tony。")
        self.assertTrue(chunks[-1].is_final)
        self.assertEqual(chunks[-1].metadata["model"], "deepseek-chat-test")
        self.assertIn("provider_timing", chunks[0].metadata)
        self.assertIn("prompt_build_ms", chunks[0].metadata["provider_timing"])

    def test_tc_phase33_010_direct_llm_bridge_with_deepseek_provider_preserves_loop(self):
        provider = DeepSeekProvider(api_key="test-key", client=FakeOpenAICompatibleClient())
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="deepseek_provider")
        loop = ConversationLoop(bridge=bridge)

        result = loop.run_text_turn_realtime_speech("Julia，你是谁？")

        self.assertEqual(result.state_history[-1], ConversationState.LISTENING)
        self.assertEqual(result.turn.assistant.cognitive_backend, "deepseek_provider")
        self.assertIn("Julia", result.turn.assistant.text)
        self.assertIn("Tony", result.turn.assistant.text)
        self.assertIn("[TTS_SENTENCE:0:local_tts]", "\n".join(result.event_log))
        trace = result.trace.to_dict()
        self.assertEqual(trace["reasoning"]["backend"], "deepseek_provider")
        self.assertIn("bridge_timing", trace["reasoning"]["metadata"])
        self.assertIn("provider_timing", trace["reasoning"]["metadata"])

    def test_tc_phase33_011_deepseek_provider_without_key_returns_structured_error(self):
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_deepseek_no_key", current_backend="deepseek_provider")
        provider = DeepSeekProvider(api_key="", client=None)

        response = provider.generate(context)

        self.assertFalse(response.ok)
        self.assertEqual(response.provider, "deepseek_provider")
        self.assertIn("DEEPSEEK_API_KEY", response.error)


if __name__ == "__main__":
    unittest.main()
