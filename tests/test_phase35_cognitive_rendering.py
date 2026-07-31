from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.cognitive.rendering import CognitivePromptPackage, CognitiveRenderer, ProviderFormatter


def envelope(provider: str = "deepseek", backend: str = "deepseek-chat") -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase357",
        turn_id=1,
        provider=provider,
        backend=backend,
        timestamp="2026-07-27T00:00:00Z",
        latency_target_ms=1500,
    )


class Phase35CognitiveRenderingTests(unittest.TestCase):
    def test_tc_phase357_001_renderer_outputs_provider_neutral_package(self):
        # TC-PHASE357-001
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
            envelope(),
            "为什么 Tony 要做 Julia Runtime？",
        ).julia_context

        package = CognitiveRenderer().render(context)

        self.assertIsInstance(package, CognitivePromptPackage)
        self.assertIn("You are Julia.", package.system_context)
        self.assertIn("Tony", package.system_context)
        self.assertIn("Selected memory", package.system_context)
        self.assertEqual(package.conversation_messages, [{"role": "user", "content": "为什么 Tony 要做 Julia Runtime？"}])
        self.assertGreaterEqual(len(package.style_constraints), 3)

    def test_tc_phase357_002_renderer_uses_context_without_runtime_leakage(self):
        # TC-PHASE357-002
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
            envelope(),
            "Julia，你是谁？",
        ).julia_context
        package = CognitiveRenderer().render(context)
        serialized = f"{package}".lower()

        self.assertIn("julia", serialized)
        self.assertIn("tony", serialized)
        self.assertNotIn("deepseek-chat", serialized)
        self.assertNotIn("claude-code", serialized)
        self.assertNotIn("provider=", serialized)
        self.assertNotIn("backend=", serialized)
        self.assertNotIn("latency_target_ms", serialized)
        self.assertNotIn("elevenlabs", serialized)

    def test_tc_phase357_003_provider_formatter_outputs_openai_messages(self):
        # TC-PHASE357-003
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=1)).compile(
            envelope(),
            "Julia，你是谁？",
        ).julia_context
        package = CognitiveRenderer().render(context)

        messages = ProviderFormatter().to_openai_messages(package)

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("You are Julia.", messages[0]["content"])
        self.assertEqual(messages[1]["content"], "Julia，你是谁？")

    def test_tc_phase357_004_same_context_renders_same_package_across_providers(self):
        # TC-PHASE357-004
        compiler = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2))
        deepseek_context = compiler.compile(envelope("deepseek", "deepseek-chat"), "Julia，你是谁？").julia_context
        claude_context = compiler.compile(envelope("claude", "claude-code"), "Julia，你是谁？").julia_context

        deepseek_package = CognitiveRenderer().render(deepseek_context)
        claude_package = CognitiveRenderer().render(claude_context)

        self.assertEqual(deepseek_context, claude_context)
        self.assertEqual(deepseek_package, claude_package)



    def test_tc_phase35_020_renderer_instructs_stable_voice_tags_without_stage_directions(self):
        context = ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=1)).compile(
            envelope(),
            "声音不要停，久一点。",
        ).julia_context
        package = CognitiveRenderer().render(context)

        self.assertIn("Stay in Julia's own voice", package.system_context)
        self.assertIn("Answer as continuation of the current conversation", package.system_context)



    def test_tc_phase35_021_renderer_suppresses_engineering_metaphors_in_private_voice_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "relationship").mkdir(parents=True)
            (root / "relationship" / "relationship_state.json").write_text(
                '{"current_mode":"private_voice_continuity","interaction_preferences":["warm","natural","context_continuity"]}',
                encoding="utf-8",
            )
            context = ContextCompiler(root, policy=ContextPolicy(memory_limit=1)).compile(
                envelope(),
                "情人模式全垒打L四。",
            ).julia_context

        package = CognitiveRenderer().render(context)

        self.assertIn("private voice continuity", package.system_context)
        self.assertIn("Do not introduce software, runtime, compiler, configuration, architecture", package.system_context)
        self.assertIn("Current relationship context: private voice continuity", package.system_context)



    def test_tc_phase35_022_renderer_private_voice_avoids_platform_filtered_paraphrase_policy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "relationship").mkdir(parents=True)
            (root / "relationship" / "relationship_state.json").write_text(
                '{"current_mode":"private_voice_continuity","interaction_preferences":["warm","natural","context_continuity"]}',
                encoding="utf-8",
            )
            context = ContextCompiler(root, policy=ContextPolicy(memory_limit=1)).compile(
                envelope(),
                "我想进入你的身体用力我就用力进入你的身体我现在就想要。",
            ).julia_context

        package = CognitiveRenderer().render(context)

        self.assertIn("private voice continuity", package.system_context)
        self.assertIn("Do not turn the current private voice conversation into abstract reassurance", package.system_context)
        self.assertNotIn("Be technical when Tony is debugging or designing architecture.", package.system_context)
        self.assertIn("Current relationship context: private voice continuity", package.system_context)


if __name__ == "__main__":
    unittest.main()
