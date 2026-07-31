import unittest

from runtime.context_os.benchmark import ContextOSIntegrationBenchmark


class TestPhase361015ContextOSIntegrationBenchmark(unittest.TestCase):
    def test_tc_361015_001_long_session_test_preserves_tail_and_prepares_compact(self):
        scenario = ContextOSIntegrationBenchmark().long_session_test()

        self.assertTrue(scenario.passed)
        self.assertEqual({m.name for m in scenario.metrics}, {"tail_preservation", "compact_preparation"})

    def test_tc_361015_002_multi_session_resurrection_test_restores_phase_consistently(self):
        scenario = ContextOSIntegrationBenchmark().multi_session_resurrection_test()

        self.assertTrue(scenario.passed)
        self.assertEqual(scenario.score, 1.0)

    def test_tc_361015_003_compact_recovery_test_restores_task_from_compact_and_state(self):
        scenario = ContextOSIntegrationBenchmark().compact_recovery_test()

        self.assertTrue(scenario.passed)
        self.assertTrue(any(m.name == "compact_loaded" and m.score == 1.0 for m in scenario.metrics))

    def test_tc_361015_004_evidence_accuracy_test_filters_assistant_noise(self):
        scenario = ContextOSIntegrationBenchmark().evidence_accuracy_test()

        self.assertTrue(scenario.passed)
        noise_metric = next(m for m in scenario.metrics if m.name == "assistant_noise_filtered")
        self.assertEqual(noise_metric.score, 1.0)

    def test_tc_361015_005_identity_drift_test_blocks_all_provider_drift_attempts(self):
        scenario = ContextOSIntegrationBenchmark().identity_drift_test()

        self.assertTrue(scenario.passed)
        blocked_metric = next(m for m in scenario.metrics if m.name == "drift_attempts_blocked")
        self.assertEqual(blocked_metric.details["blocked"], 100)

    def test_tc_361015_006_provider_migration_test_keeps_context_stable(self):
        scenario = ContextOSIntegrationBenchmark().provider_migration_test()

        self.assertTrue(scenario.passed)
        self.assertEqual(scenario.score, 1.0)

    def test_tc_361015_007_full_benchmark_report_gate_ready(self):
        report = ContextOSIntegrationBenchmark().run_all()
        data = report.to_dict()

        self.assertTrue(report.gate_ready)
        self.assertEqual(len(report.scenarios), 6)
        self.assertEqual(report.total_score, 1.0)
        self.assertTrue(data["gate_ready"])


if __name__ == "__main__":
    unittest.main()
