from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.situation import SituationContext, SituationRuntime


class Phase35SituationRuntimeTests(unittest.TestCase):
    def test_tc_phase354_001_situation_context_has_no_memory_or_runtime_fields(self):
        # TC-PHASE354-001
        fields = set(SituationContext.__dataclass_fields__.keys())

        self.assertEqual(
            fields,
            {
                "current_activity",
                "environment",
                "goal",
                "interaction_mode",
                "active_topics",
            },
        )
        forbidden = {
            "memory_content",
            "relationship_history",
            "backend",
            "provider",
            "runtime",
            "model",
            "latency",
            "tts",
            "session_id",
            "turn_id",
            "emotion_score",
        }
        self.assertTrue(fields.isdisjoint(forbidden))

    def test_tc_phase354_002_situation_runtime_returns_current_building_context(self):
        # TC-PHASE354-002
        context = SituationRuntime(ROOT).build_context()

        self.assertEqual(context.current_activity, "building Julia Cognitive Environment")
        self.assertEqual(context.environment, "software_architecture")
        self.assertIn("Claude implicit cognitive environment", context.goal)
        self.assertEqual(context.interaction_mode, "engineering_collaboration")
        self.assertIn("Julia Runtime", context.active_topics)
        self.assertIn("Phase 3.5", context.active_topics)

    def test_tc_phase354_003_situation_mode_switch_changes_context_without_provider_state(self):
        # TC-PHASE354-003
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            situation_dir = root / "situation"
            situation_dir.mkdir(parents=True)
            (situation_dir / "situation_state.json").write_text(
                json.dumps(
                    {
                        "current_activity": "explaining JuliaContext v2",
                        "environment": "architecture_review",
                        "goal": "clarify context compiler contract",
                        "interaction_mode": "technical_explanation",
                        "active_topics": ["JuliaContext v2", "Context Compiler"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            context = SituationRuntime(root).build_context()

        self.assertEqual(context.current_activity, "explaining JuliaContext v2")
        self.assertEqual(context.environment, "architecture_review")
        self.assertEqual(context.interaction_mode, "technical_explanation")
        self.assertIn("Context Compiler", context.active_topics)
        serialized = str(context).lower()
        self.assertNotIn("deepseek", serialized)
        self.assertNotIn("claude", serialized)
        self.assertNotIn("provider", serialized)
        self.assertNotIn("backend", serialized)

    def test_tc_phase354_004_situation_runtime_switches_private_voice_context_from_persistent_mode(self):
        context = SituationRuntime(ROOT).build_context("private_voice_continuity")

        self.assertEqual(context.environment, "private_voice_conversation")
        self.assertEqual(context.interaction_mode, "private_voice_continuity")
        self.assertNotIn("Julia Runtime", context.active_topics)
        self.assertNotIn("software", str(context).lower())

    def test_tc_phase354_005_situation_runtime_does_not_keyword_match_user_input(self):
        context = SituationRuntime(ROOT).build_context("情人模式全垒打L四。")

        self.assertEqual(context.environment, "software_architecture")
        self.assertEqual(context.interaction_mode, "情人模式全垒打L四。")



if __name__ == "__main__":
    unittest.main()
