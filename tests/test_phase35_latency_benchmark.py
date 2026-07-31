from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.benchmark import LatencyBenchmarkRunner
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider
from runtime.cognitive.provider.openai_compatible import OpenAICompatibleChunk, OpenAICompatibleResult


class TimedFakeClient:
    def chat(self, messages):
        return OpenAICompatibleResult(
            text="我是Julia，Tony。",
            model="timed-model",
            latency_ms=100,
            timings={"prompt_input_chars": 1234, "provider_first_token_ms": 80},
        )

    def stream_chat(self, messages):
        yield OpenAICompatibleChunk(
            text="我是Julia，Tony。",
            index=0,
            is_final=True,
            model="timed-model",
            latency_ms=120,
            timings={
                "http_response_open_ms": 30,
                "provider_first_token_ms": 80,
                "provider_chunk_ms": 120,
                "provider_total_ms": 120,
            },
        )


class Phase35LatencyBenchmarkTests(unittest.TestCase):
    def loop_factory(self):
        provider = DeepSeekProvider(api_key="test-key", client=TimedFakeClient())
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="deepseek_provider")
        return ConversationLoop(bridge=bridge)

    def test_tc_phase35_012_latency_benchmark_collects_repeated_turn_metrics(self):
        report = LatencyBenchmarkRunner(self.loop_factory).run(text="Julia，你是谁？", repeat=2)

        self.assertEqual(report.count, 2)
        data = report.to_dict()
        self.assertEqual(data["summary"]["provider_first_token_ms"]["median"], 80.0)
        self.assertEqual(data["summary"]["boundary_count"], 0)
        self.assertEqual(data["samples"][0]["backend"], "deepseek_provider")
        self.assertGreater(data["samples"][0]["prompt_input_chars"], 0)

    def test_tc_phase35_013_latency_benchmark_report_is_router_ready(self):
        report = LatencyBenchmarkRunner(self.loop_factory).run(text="Julia，用短句回答。", repeat=1)
        summary = report.summary()

        self.assertIn("prompt_input_chars", summary)
        self.assertIn("http_response_open_ms", summary)
        self.assertIn("provider_first_token_ms", summary)
        self.assertIn("time_to_first_voice_ms", summary)

    def test_tc_phase35_014_latency_benchmark_fast_ack_reduces_reported_ttfv(self):
        report = LatencyBenchmarkRunner(self.loop_factory).run(
            text="Julia，你是谁？",
            repeat=1,
            fast_ack_text="嗯，Tony，我在想。",
        )
        sample = report.samples[0]

        self.assertLessEqual(sample.time_to_first_voice_ms, sample.provider_first_token_ms)
        self.assertEqual(report.to_dict()["samples"][0]["boundary_detected"], False)


if __name__ == "__main__":
    unittest.main()
