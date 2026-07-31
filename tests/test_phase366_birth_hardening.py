from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
from tts.chunking import SentenceSegmenter, split_for_tts


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_birth_hardening",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase366FakeMessageProvider(LLMProvider):
    def info(self) -> ProviderInfo:
        return ProviderInfo(name="deepseek", model="fake-deepseek", supports_stream=True)

    def generate(self, context):
        return LLMResponse(text="legacy path", provider="fake")

    def generate_messages(self, messages):
        return LLMResponse(text="Tony，我在。", provider="deepseek_provider", metadata={"provider_info": self.info().to_dict()})

    def stream_messages(self, messages):
        yield LLMChunk(text="Tony，我在。", provider="deepseek_provider", index=0, is_final=True, metadata={"provider_info": self.info().to_dict()})


class Phase366BirthHardeningTests(unittest.TestCase):
    def test_tc_phase3661_001_context_uses_cognitive_memory_trace_for_julia_runtime_semantics(self):
        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3))
        turn = compiler.compile(envelope(), "Julia最近我们一直在做什么。")
        joined = "\n".join(memory.summary for memory in turn.julia_context.memory_context)
        trace_joined = str(compiler.last_memory_trace)

        self.assertIn("AI Cognitive Runtime", joined)
        self.assertIn("not the Julia programming language runtime", joined)
        self.assertIn("memory_project_semantic_julia_runtime_ai_cognitive_runtime", trace_joined)
        self.assertNotIn("@code_typed", joined)

    def test_tc_phase3661_002_direct_bridge_emits_identity_mode_memory_trace(self):
        bridge = DirectLLMBridge(project_root=ROOT, provider=Phase366FakeMessageProvider(), current_backend="deepseek_provider")
        loop = ConversationLoop(bridge=bridge)
        result = loop.run_text_turn_realtime_speech("Julia，你是谁？")
        metadata = result.turn.assistant.metadata

        self.assertTrue(metadata["phase35_pipeline"])
        self.assertEqual(metadata["identity_integrity"]["persona"], "Julia")
        self.assertEqual(metadata["identity_integrity"]["user"], "Tony")
        self.assertFalse(metadata["identity_integrity"]["host_dependency"])
        self.assertIn("cognitive_mode", metadata)
        self.assertIn("memory_trace", metadata)
        self.assertIsInstance(metadata["memory_trace"]["retrieved"], list)

    def test_tc_phase3661_003_stt_normalizes_julia_and_tony_proper_nouns_only(self):
        stt = SpeechLabSTT(SpeechLabSTTConfig(speech_lab_root=Path("/Users/admin/Desktop/speech_lab")))

        self.assertEqual(stt._normalize_text("助力呀你是谁。"), "Julia你是谁。")
        self.assertEqual(stt._normalize_text("Julia偷你最感动你的地方是什么。"), "JuliaTony最感动你的地方是什么。")
        self.assertEqual(stt._normalize_text("Julia你知道偷是谁吗你。"), "Julia你知道Tony是谁吗你。")

    def test_tc_phase3661_004_voice_text_sanitizer_removes_markdown_stage_directions_and_number_splits(self):
        chunks = split_for_tts("（轻笑）我建议：\n\n1. **确认现有架构**。2. `ContextCompiler`。", max_chars=80)
        spoken = "".join(chunks)

        self.assertNotIn("**", spoken)
        self.assertNotIn("`", spoken)
        self.assertNotIn("（轻笑）", spoken)
        self.assertIn("第一，确认现有架构。", spoken)
        self.assertIn("第二，ContextCompiler。", spoken)

    def test_tc_phase3661_005_realtime_segmenter_does_not_emit_number_only_sentence(self):
        segmenter = SentenceSegmenter(max_chars=80)
        emitted = []
        for piece in ["我建议三步：\n\n", "1", ". **确认", "现有架构**。"]:
            emitted.extend(segmenter.push(piece))
        emitted.extend(segmenter.flush())

        self.assertEqual(emitted, ["我建议三步：\n第一，确认现有架构。"])


if __name__ == "__main__":
    unittest.main()
