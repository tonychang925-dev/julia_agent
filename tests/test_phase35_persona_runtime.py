from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.persona import PersonaCompiler, PersonaContext, PersonaLoader


class Phase35PersonaRuntimeTests(unittest.TestCase):
    def test_tc_phase351_001_persona_context_has_no_runtime_fields(self):
        # TC-PHASE351-001
        fields = set(PersonaContext.__dataclass_fields__.keys())

        self.assertEqual(
            fields,
            {
                "name",
                "identity_summary",
                "speaking_style",
                "values",
                "communication_preferences",
            },
        )
        forbidden = {"backend", "provider", "runtime", "model", "latency", "tts", "session_id", "turn_id"}
        self.assertTrue(fields.isdisjoint(forbidden))

    def test_tc_phase351_002_persona_loader_reads_identity_without_provider_state(self):
        # TC-PHASE351-002
        source = PersonaLoader(ROOT).load()

        self.assertEqual(source.identity_yaml["identity"]["name"], "Julia")
        self.assertIn("Julia Personality", source.personality_text)
        self.assertIn("Julia Values", source.values_text)
        self.assertIn("Julia Conversation Contract", source.conversation_contract_text)
        combined = f"{source.identity_yaml} {source.personality_text} {source.values_text} {source.conversation_contract_text}"
        self.assertNotIn("deepseek_provider", combined)
        self.assertNotIn("current_backend", combined)
        self.assertNotIn("latency_target_ms", combined)

    def test_tc_phase351_003_persona_compiler_outputs_stable_julia_context(self):
        # TC-PHASE351-003
        context = PersonaCompiler().compile(PersonaLoader(ROOT).load())

        self.assertEqual(context.name, "Julia")
        self.assertIn("Tony", context.identity_summary)
        self.assertIn("Julia", context.identity_summary)
        self.assertIn("warm", context.speaking_style)
        self.assertIn("thoughtful", context.speaking_style)
        self.assertIn("Chinese-first", context.speaking_style)
        self.assertIn("maintain continuity", context.values)
        self.assertIn("be technical when Tony is debugging or designing architecture", context.communication_preferences)
        serialized = str(context)
        self.assertNotIn("deepseek", serialized.lower())
        self.assertNotIn("provider", serialized.lower())
        self.assertNotIn("runtime_state", serialized.lower())


if __name__ == "__main__":
    unittest.main()
