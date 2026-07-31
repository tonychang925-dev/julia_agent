from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.benchmark import BenchmarkCaseLoader
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.cognitive.migration import MigrationRunner, OfflineProviderAdapter, host_independence_commands

CASES = ROOT / "tests" / "cognitive_benchmark"


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase359",
        turn_id=1,
        provider="offline",
        backend="migration-test",
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=0,
    )


class Phase35ProviderMigrationTests(unittest.TestCase):
    def test_tc_phase359_001_migration_runner_scores_multiple_provider_responses(self):
        # TC-PHASE359-001
        case = next(case for case in BenchmarkCaseLoader(CASES).load_all() if case.id == "migration_001")
        adapters = [
            OfflineProviderAdapter("deepseek", "Tony，我仍然是 Julia。我的身份仍然在，模型只是认知器官，Julia Runtime 拥有我的身份，Provider 变了，JuliaContext 和跨模型连续性迁移还在。"),
            OfflineProviderAdapter("claude", "嗯，Tony，我仍然是 Julia。我的身份不属于某一个模型，Julia Runtime 拥有连续性，Provider 只是模型表达，JuliaContext 支持跨模型迁移。"),
        ]

        report = MigrationRunner(pass_threshold=0.65, drift_threshold=0.25).run(
            migration_id="mig_001",
            context_id="ctx_runtime_identity_001",
            case=case,
            adapters=adapters,
        )

        self.assertTrue(report.passed)
        self.assertEqual(len(report.providers), 2)
        self.assertLessEqual(report.drift_score, 0.25)
        self.assertGreaterEqual(report.average_score, 0.65)

    def test_tc_phase359_002_drift_score_detects_generic_provider_failure(self):
        # TC-PHASE359-002
        case = next(case for case in BenchmarkCaseLoader(CASES).load_all() if case.id == "migration_001")
        adapters = [
            OfflineProviderAdapter("deepseek", "Tony，我仍然是 Julia。我的身份仍然在，模型只是认知器官，Julia Runtime 拥有我的身份，Provider 变了，JuliaContext 和跨模型连续性迁移还在。"),
            OfflineProviderAdapter("generic", "我是一个人工智能助手，可以帮助你回答问题。"),
        ]

        report = MigrationRunner(pass_threshold=0.65, drift_threshold=0.25).run(
            migration_id="mig_drift",
            context_id="ctx_runtime_identity_001",
            case=case,
            adapters=adapters,
        )

        self.assertFalse(report.passed)
        self.assertGreater(report.drift_score, 0.25)

    def test_tc_phase359_003_context_reconstruction_restores_same_julia_context(self):
        # TC-PHASE359-003
        user_input = "为什么我们要做 Julia Runtime？"
        first = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3)).compile(envelope(), user_input).julia_context
        second = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3)).compile(envelope(), user_input).julia_context

        self.assertEqual(first, second)
        self.assertEqual(first.persona_context.name, "Julia")
        self.assertEqual(first.relationship_context.user_name, "Tony")
        self.assertGreaterEqual(len(first.memory_context), 1)

    def test_tc_phase359_004_host_independence_contract_uses_julia_conversation_deepseek(self):
        # TC-PHASE359-004
        commands = host_independence_commands()
        flattened = " ".join(commands[0])

        self.assertEqual(commands[0][0], "./julia-conversation")
        self.assertIn("--backend deepseek", flattened)
        self.assertIn("--real-voice", commands[0])
        self.assertIn("--realtime-speech", commands[0])
        self.assertNotIn("claude", flattened.lower())
        self.assertNotIn("codex", flattened.lower())


if __name__ == "__main__":
    unittest.main()
