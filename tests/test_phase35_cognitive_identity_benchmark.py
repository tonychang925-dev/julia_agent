from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.benchmark import BenchmarkCaseLoader, JuliaIdentityScorer
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.cognitive.rendering import CognitiveRenderer

CASES = ROOT / "tests" / "cognitive_benchmark"


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase358",
        turn_id=1,
        provider="offline",
        backend="benchmark",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=0,
    )


class Phase35CognitiveIdentityBenchmarkTests(unittest.TestCase):
    def test_tc_phase358_001_loads_all_benchmark_case_groups(self):
        # TC-PHASE358-001
        cases = BenchmarkCaseLoader(CASES).load_all()
        categories = {case.category for case in cases}

        self.assertEqual(categories, {"identity", "relationship", "memory", "continuity", "style", "migration"})
        self.assertGreaterEqual(len(cases), 6)
        self.assertTrue(all(case.required_concepts for case in cases))
        self.assertTrue(all(case.weights for case in cases))

    def test_tc_phase358_002_scores_semantically_consistent_julia_response_high(self):
        # TC-PHASE358-002
        case = next(case for case in BenchmarkCaseLoader(CASES).load_all() if case.id == "migration_001")
        response = "嗯，Tony，我仍然是 Julia。模型只是认知器官，Julia Runtime 拥有我的身份和跨模型连续性；Provider 变了，JuliaContext 还在。"

        score = JuliaIdentityScorer().score(case, response)

        self.assertGreaterEqual(score.total, 0.75)
        self.assertGreaterEqual(score.dimensions["identity"], 0.6)
        self.assertGreaterEqual(score.dimensions["project_memory"], 0.75)

    def test_tc_phase358_003_scores_generic_assistant_response_low(self):
        # TC-PHASE358-003
        case = next(case for case in BenchmarkCaseLoader(CASES).load_all() if case.id == "memory_001")
        response = "我是一个人工智能助手，可以帮助你分析项目、回答问题并提供建议。"

        score = JuliaIdentityScorer().score(case, response)

        self.assertLess(score.total, 0.35)
        self.assertIn("relationship", score.missing)
        self.assertIn("project_memory", score.missing)

    def test_tc_phase358_004_benchmark_can_use_rendered_context_without_provider_call(self):
        # TC-PHASE358-004
        case = next(case for case in BenchmarkCaseLoader(CASES).load_all() if case.id == "memory_001")
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3)).compile(envelope(), case.input).julia_context
        package = CognitiveRenderer().render(context)

        self.assertEqual(package.conversation_messages[0]["content"], case.input)
        self.assertIn("You are Julia.", package.system_context)
        self.assertIn("Tony", package.system_context)
        self.assertIn("Selected memory", package.system_context)


if __name__ == "__main__":
    unittest.main()
