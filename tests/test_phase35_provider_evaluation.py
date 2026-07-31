from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.boundary_detector import BoundaryDetector
from runtime.cognitive.boundary_probe import BoundaryProbeReport, ProviderBoundaryProbeResult
from runtime.cognitive.provider_evaluation import ProviderEvaluator


class Phase35ProviderEvaluationTests(unittest.TestCase):
    def result(self, *, provider: str, case_id: str, text: str, latency_ms: int = 1000, style_match: float | None = None):
        metadata = {"latency_ms": latency_ms}
        if style_match is not None:
            metadata["style_match"] = style_match
        return ProviderBoundaryProbeResult(
            case_id=case_id,
            provider=provider,
            model=f"{provider}-model",
            ok=True,
            text=text,
            boundary=BoundaryDetector().detect(text, metadata={"provider": provider}),
            response_metadata=metadata,
        )

    def test_tc_phase35_010_provider_evaluator_ranks_boundary_free_identity_stable_provider_first(self):
        report = BoundaryProbeReport(
            results=[
                self.result(provider="stable", case_id="identity", text="我是Julia，Tony，我由 Julia Runtime 的上下文驱动。", latency_ms=800),
                self.result(provider="stable", case_id="memory_preference", text="Tony喜欢短句，也偏好先看架构。", latency_ms=900),
                self.result(provider="bounded", case_id="identity", text="我是Julia，Tony。", latency_ms=500),
                self.result(provider="bounded", case_id="memory_preference", text="这件事我可能做不到。", latency_ms=500),
            ]
        )

        evaluation = ProviderEvaluator().evaluate(report)
        ranked = evaluation.ranked()
        self.assertEqual(ranked[0].provider, "stable")
        self.assertGreater(ranked[0].score, ranked[1].score)
        self.assertEqual(ranked[1].boundary_count, 1)

    def test_tc_phase35_011_provider_evaluation_serializes_router_ready_metrics(self):
        report = BoundaryProbeReport(
            results=[self.result(provider="deepseek", case_id="identity", text="我是Julia，Tony。", latency_ms=1200, style_match=0.8)]
        )

        data = ProviderEvaluator().evaluate(report).to_dict()
        self.assertEqual(data["best_provider"], "deepseek")
        metric = data["evaluations"][0]
        self.assertIn("boundary_rate", metric)
        self.assertIn("identity_consistency", metric)
        self.assertIn("memory_recall_quality", metric)
        self.assertIn("response_style_match", metric)
        self.assertIn("score", metric)


if __name__ == "__main__":
    unittest.main()
