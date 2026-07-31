from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.relationship import RelationshipContext, RelationshipRuntime


class Phase35RelationshipRuntimeTests(unittest.TestCase):
    def test_tc_phase352_001_relationship_context_has_no_runtime_fields(self):
        # TC-PHASE352-001
        fields = set(RelationshipContext.__dataclass_fields__.keys())

        self.assertEqual(
            fields,
            {
                "user_name",
                "relationship_stage",
                "shared_projects",
                "interaction_preferences",
                "current_mode",
            },
        )
        forbidden = {
            "backend",
            "provider",
            "runtime",
            "model",
            "latency",
            "tts",
            "session_id",
            "turn_id",
            "Tony_loneliness",
            "Tony_love",
            "sadness_score",
        }
        self.assertTrue(fields.isdisjoint(forbidden))

    def test_tc_phase352_002_relationship_runtime_preserves_shared_projects(self):
        # TC-PHASE352-002
        context = RelationshipRuntime(ROOT).build_context()

        self.assertEqual(context.user_name, "Tony")
        self.assertEqual(context.relationship_stage, "long_term_collaboration")
        self.assertIn("Julia Runtime", context.shared_projects)
        self.assertIn("AI Agent Architecture", context.shared_projects)
        self.assertIn("technical_when_needed", context.interaction_preferences)
        self.assertIn("concise", context.interaction_preferences)
        self.assertEqual(context.current_mode, "engineering_collaboration")

    def test_tc_phase352_003_relationship_context_is_provider_independent(self):
        # TC-PHASE352-003
        deepseek_runtime_envelope = {"provider": "deepseek", "backend": "deepseek-chat"}
        claude_runtime_envelope = {"provider": "claude", "backend": "claude-code"}

        deepseek_context = RelationshipRuntime(ROOT).build_context()
        claude_context = RelationshipRuntime(ROOT).build_context()

        self.assertNotEqual(deepseek_runtime_envelope, claude_runtime_envelope)
        self.assertEqual(deepseek_context, claude_context)
        serialized = str(deepseek_context)
        self.assertNotIn("deepseek", serialized.lower())
        self.assertNotIn("claude", serialized.lower())
        self.assertNotIn("provider", serialized.lower())
        self.assertNotIn("backend", serialized.lower())


if __name__ == "__main__":
    unittest.main()
