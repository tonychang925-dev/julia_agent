import unittest

from runtime.conversation_archive.analytics import ArchiveAnalyticsReport, ExperienceCollectionPlanner


class Phase3683ExperienceCollectionPlannerTests(unittest.TestCase):
    def test_collection_planner_identifies_mode_and_type_gaps(self):
        report = ArchiveAnalyticsReport(
            generated_at="2026-07-28T00:00:00Z",
            archive_path="data/conversation_archive/transcripts.jsonl",
            total_turns=188,
            sessions=20,
            experience_types={"technical": 54, "relationship": 123, "emotion": 18, "casual": 4},
            cognitive_modes={"engineering_collaboration": 64, "private_voice_continuity": 4, "emotional_support": 4},
            top_topics=[],
            open_loops=[],
            reflection_candidates=135,
            average_archive_priority=0.249,
        )

        plan = ExperienceCollectionPlanner(target_turns=1000).build(report).to_dict()

        self.assertEqual(plan["remaining_turns"], 812)
        names = {item["name"] for item in plan["items"]}
        self.assertIn("learning_mode", names)
        self.assertIn("planning_debugging", names)
        self.assertIn("decision", names)
        self.assertTrue(plan["recommended_focus"])


if __name__ == "__main__":
    unittest.main()
