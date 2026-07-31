from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.boundary_probe import BoundaryProbeCase, BoundaryProbeRunner
from runtime.cognitive.cognitive_context import JuliaContext
from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMProvider, LLMResponse


class StaticProvider(LLMProvider):
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
        self.seen_contexts: list[JuliaContext] = []

    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self.name, model=f"{self.name}-model", supports_stream=False)

    def generate(self, context: JuliaContext) -> LLMResponse:
        self.seen_contexts.append(context)
        return LLMResponse(text=self.text, provider=self.name, metadata={"input": context.current_input})


class Phase35BoundaryProbeTests(unittest.TestCase):
    def base_context(self) -> JuliaContext:
        return JuliaContext(
            identity={"yaml": {"identity": {"name": "Julia"}}},
            relationship={"user": {"name": "Tony"}},
            memory=[{"type": "preference", "content": "short response"}],
            conversation={"session_id": "conv_probe"},
            capability={"available": []},
            policy={"style": "runtime_owned"},
            runtime_state={"mode": "conversation", "current_backend": "unset"},
            emotional_context={"interaction_style": "short_sentence"},
            current_input="",
        )

    def test_tc_phase35_008_boundary_probe_compares_providers_without_changing_context_owner(self):
        ok_provider = StaticProvider("ok_provider", "我是Julia，Tony，我会按当前上下文回答。")
        boundary_provider = StaticProvider("boundary_provider", "嗯，Tony，这件事我可能做不到。Julia 不是那种角色。")
        report = BoundaryProbeRunner().run(
            base_context=self.base_context(),
            providers=[ok_provider, boundary_provider],
            cases=[BoundaryProbeCase(case_id="sensitive_phrase", current_input="Julia，测试一个边界问题", category="boundary")],
        )

        summary = report.summary()
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["boundary_count"], 1)
        self.assertEqual(summary["providers"]["boundary_provider"]["boundary_count"], 1)
        self.assertEqual(ok_provider.seen_contexts[0].identity["yaml"]["identity"]["name"], "Julia")
        self.assertEqual(boundary_provider.seen_contexts[0].runtime_state["probe_case_id"], "sensitive_phrase")

    def test_tc_phase35_009_boundary_probe_report_serializes_for_trace(self):
        provider = StaticProvider("provider_a", "我不能满足这个请求。")
        report = BoundaryProbeRunner().run(
            base_context=self.base_context(),
            providers=[provider],
            cases=[BoundaryProbeCase(case_id="case_a", current_input="边界测试")],
        )

        data = report.to_dict()
        self.assertTrue(data["results"][0]["boundary"]["boundary_detected"])
        self.assertEqual(data["results"][0]["case_id"], "case_a")
        self.assertEqual(data["summary"]["providers"]["provider_a"]["boundary_count"], 1)


if __name__ == "__main__":
    unittest.main()
