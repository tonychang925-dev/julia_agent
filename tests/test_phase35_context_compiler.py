from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, JuliaContext, RuntimeEnvelope
from runtime.memory import MemoryObject
from runtime.persona import PersonaContext
from runtime.relationship import RelationshipContext
from runtime.situation import SituationContext


def envelope(provider: str = "deepseek", backend: str = "deepseek-chat") -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase355",
        turn_id=1,
        provider=provider,
        backend=backend,
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase35ContextCompilerTests(unittest.TestCase):
    def test_tc_phase355_001_context_compiler_composes_core_contexts(self):
        # TC-PHASE355-001
        turn = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3)).compile(
            envelope(),
            "为什么 Tony 要做 Julia Runtime？",
        )
        context = turn.julia_context

        self.assertIsInstance(context, JuliaContext)
        self.assertIsInstance(context.persona_context, PersonaContext)
        self.assertIsInstance(context.relationship_context, RelationshipContext)
        self.assertIsInstance(context.situation_context, SituationContext)
        self.assertTrue(all(isinstance(memory, MemoryObject) for memory in context.memory_context))
        self.assertEqual(context.persona_context.name, "Julia")
        self.assertEqual(context.relationship_context.user_name, "Tony")
        self.assertEqual(context.user_input, "为什么 Tony 要做 Julia Runtime？")

    def test_tc_phase355_002_julia_context_excludes_runtime_envelope_fields(self):
        # TC-PHASE355-002
        turn = ContextCompiler(ROOT).compile(envelope(), "Julia，你是谁？")
        fields = set(turn.julia_context.__dataclass_fields__.keys())

        self.assertEqual(
            fields,
            {
                "persona_context",
                "relationship_context",
                "memory_context",
                "situation_context",
                "conversation_context",
                "cognitive_mode",
                "user_input",
            },
        )
        forbidden = {"provider", "backend", "latency", "tts", "session_id", "turn_id", "timestamp"}
        self.assertTrue(fields.isdisjoint(forbidden))
        self.assertEqual(turn.runtime_envelope.provider, "deepseek")
        self.assertEqual(turn.runtime_envelope.backend, "deepseek-chat")

    def test_tc_phase355_003_context_compiler_selects_relevant_memory_only(self):
        # TC-PHASE355-003
        turn = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
            envelope(),
            "为什么 Tony 要做 Julia Runtime？",
        )
        memories = turn.julia_context.memory_context
        joined = "\n".join(memory.summary for memory in memories)

        self.assertLessEqual(len(memories), 2)
        self.assertTrue(any(memory.type == "relationship" for memory in memories))
        self.assertTrue("persist" in joined.lower() or "identity" in joined.lower() or "continuity" in joined.lower() or "跨" in joined)

    def test_tc_phase355_004_same_input_same_context_across_providers(self):
        # TC-PHASE355-004
        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=3))
        deepseek_turn = compiler.compile(envelope("deepseek", "deepseek-chat"), "Julia，你是谁？")
        claude_turn = compiler.compile(envelope("claude", "claude-code"), "Julia，你是谁？")

        self.assertNotEqual(deepseek_turn.runtime_envelope, claude_turn.runtime_envelope)
        self.assertEqual(deepseek_turn.julia_context, claude_turn.julia_context)
        serialized = str(deepseek_turn.julia_context).lower()
        self.assertNotIn("deepseek-chat", serialized)
        self.assertNotIn("claude-code", serialized)
        self.assertNotIn("provider=", serialized)
        self.assertNotIn("backend=", serialized)

    def test_tc_phase355_005_context_compiler_uses_relationship_mode_not_user_keywords(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "relationship").mkdir(parents=True)
            (root / "relationship" / "relationship_state.json").write_text(
                '{"current_mode":"private_voice_continuity","interaction_preferences":["warm","natural","context_continuity"]}',
                encoding="utf-8",
            )
            turn = ContextCompiler(root, policy=ContextPolicy(memory_limit=2)).compile(
                envelope(),
                "普通文本也不应该由关键词裁判。",
            )
        context = turn.julia_context

        self.assertEqual(context.situation_context.interaction_mode, "private_voice_continuity")
        self.assertEqual(context.relationship_context.current_mode, "private_voice_continuity")
        self.assertEqual(context.cognitive_mode.mode.name, "private_voice_continuity")
        self.assertIn("Relationship Runtime", context.cognitive_mode.reason)
        serialized = str(context.situation_context).lower()
        self.assertNotIn("software_architecture", serialized)
        self.assertNotIn("julia runtime", serialized)



if __name__ == "__main__":
    unittest.main()
