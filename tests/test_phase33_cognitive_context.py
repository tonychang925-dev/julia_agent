from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_builder import ContextBuilder
from runtime.cognitive.prompt_builder import PromptBuilder
from runtime.cognitive.provider.echo_provider import EchoProvider


class Phase33CognitiveContextTests(unittest.TestCase):
    def test_tc_phase33_001_context_integrity_stable_snapshot_from_persistent_state(self):
        builder = ContextBuilder(ROOT)
        context_a = builder.build(
            "Julia，你是谁？",
            session_id="conv_ctx_001",
            current_backend="echo_provider",
            conversation={"session_id": "conv_ctx_001", "turn_id": 1, "history": []},
        )
        context_b = builder.build(
            "Julia，你是谁？",
            session_id="conv_ctx_001",
            current_backend="deepseek_provider",
            conversation={"session_id": "conv_ctx_001", "turn_id": 1, "history": []},
        )

        self.assertEqual(context_a.identity["yaml"]["identity"]["name"], "Julia")
        self.assertEqual(context_a.relationship["user"]["name"], "Tony")
        self.assertEqual(context_a.current_input, "Julia，你是谁？")
        self.assertEqual(context_a.runtime_state["mode"], "conversation")
        self.assertTrue(context_a.runtime_state["voice_enabled"])
        self.assertEqual(context_a.emotional_context["interaction_style"], "short_sentence")
        # Provider/backend can change runtime_state, but persistent Julia inputs stay stable.
        self.assertEqual(context_a.identity, context_b.identity)
        self.assertEqual(context_a.relationship, context_b.relationship)
        self.assertEqual(context_a.memory, context_b.memory)
        self.assertNotEqual(context_a.runtime_state["current_backend"], context_b.runtime_state["current_backend"])

    def test_tc_phase33_002_identity_persistence_after_rebuilding_context(self):
        first = ContextBuilder(ROOT).build("Julia，你还记得我吗？", session_id="conv_restart_1")
        second = ContextBuilder(ROOT).build("Julia，你还记得我吗？", session_id="conv_restart_2")

        self.assertEqual(first.identity["yaml"]["identity"]["name"], "Julia")
        self.assertEqual(second.identity["yaml"]["identity"]["name"], "Julia")
        self.assertEqual(first.relationship["user"]["name"], "Tony")
        self.assertEqual(second.relationship["user"]["name"], "Tony")
        self.assertGreaterEqual(len(first.memory), 0)
        self.assertEqual(first.policy["language"], "Chinese")

    def test_tc_phase33_003_provider_independence_echo_uses_same_julia_context(self):
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_provider_001")
        provider = EchoProvider()
        response = provider.generate(context)
        chunks = list(provider.stream(context))

        self.assertTrue(response.ok)
        self.assertIn("我是Julia", response.text)
        self.assertIn("Tony", response.text)
        self.assertEqual(response.metadata["identity_name"], "Julia")
        self.assertEqual(response.metadata["user_name"], "Tony")
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual("".join(chunk.text for chunk in chunks), response.text)

    def test_tc_phase33_004_prompt_builder_consumes_context_without_loading_state(self):
        context = ContextBuilder(ROOT).build("Julia，你是谁？", session_id="conv_prompt_001")
        prompt = PromptBuilder().build(context)

        self.assertIn("You are Julia.", prompt.system)
        self.assertIn("speaking with Tony", prompt.system)
        self.assertIn("Conversation contract", prompt.system)
        self.assertIn("Private intimacy / relationship contract", prompt.system)
        self.assertNotIn("running as an independent Julia Runtime cognitive turn", prompt.system)
        self.assertNotIn("The model is only a cognitive provider", prompt.system)
        self.assertNotIn("current_backend", prompt.system)
        self.assertEqual(prompt.messages, [{"role": "user", "content": "Julia，你是谁？"}])
        openai_messages = prompt.to_openai_messages()
        self.assertEqual(openai_messages[0]["role"], "system")
        self.assertEqual(openai_messages[1]["role"], "user")


if __name__ == "__main__":
    unittest.main()
