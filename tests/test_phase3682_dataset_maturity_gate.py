import unittest

from runtime.conversation_archive.analytics import ArchiveAnalyticsReport, DatasetMaturityEvaluator, DatasetMaturityThresholds


class Phase3682DatasetMaturityGateTests(unittest.TestCase):
    def make_report(self, *, turns: int, sessions: int, modes: int, types: int) -> ArchiveAnalyticsReport:
        return ArchiveAnalyticsReport(
            generated_at="2026-07-28T00:00:00Z",
            archive_path="data/conversation_archive/transcripts.jsonl",
            total_turns=turns,
            sessions=sessions,
            experience_types={f"type{i}": 1 for i in range(types)},
            cognitive_modes={f"mode{i}": 1 for i in range(modes)},
            top_topics=[],
            open_loops=[],
            reflection_candidates=0,
            average_archive_priority=0.0,
        )

    def test_dataset_maturity_blocks_compaction_before_enough_experience(self):
        report = self.make_report(turns=141, sessions=12, modes=3, types=4)
        maturity = DatasetMaturityEvaluator().evaluate(report)

        self.assertFalse(maturity.ready_for_compression_design)
        self.assertEqual(maturity.recommendation, "collect_more_experience_before_compact")
        self.assertTrue(any("turns" in gap for gap in maturity.gaps))

    def test_dataset_maturity_allows_compression_design_after_thresholds(self):
        report = self.make_report(turns=1000, sessions=20, modes=4, types=5)
        maturity = DatasetMaturityEvaluator(DatasetMaturityThresholds()).evaluate(report)

        self.assertTrue(maturity.ready_for_compression_design)
        self.assertEqual(maturity.recommendation, "ready_for_phase_3_6_9")
        self.assertEqual(maturity.gaps, [])


if __name__ == "__main__":
    unittest.main()
