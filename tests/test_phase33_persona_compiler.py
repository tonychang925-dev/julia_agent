from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.context_builder import ContextBuilder
from runtime.cognitive.persona_compiler import PersonaCompiler
from runtime.cognitive.prompt_builder import PromptBuilder


class Phase33PersonaCompilerTests(unittest.TestCase):
    def test_tc_phase33_017_context_builder_loads_private_relationship_contract(self):
        context = ContextBuilder(ROOT).build("Julia，继续", session_id="conv_persona_001")

        self.assertIn("adult_intimacy_contract", context.identity)
        self.assertIn("Julia Adult Intimacy Contract", context.identity["adult_intimacy_contract"])
        self.assertIn("conversation_contract", context.identity)

    def test_tc_phase33_018_persona_compiler_separates_runtime_truth_from_persona_prompt(self):
        context = ContextBuilder(ROOT).build(
            "Julia，你是谁？",
            session_id="conv_persona_002",
            current_backend="deepseek_provider",
        )
        package = PersonaCompiler().compile(context)
        prompt = PromptBuilder().build(context)

        self.assertEqual(package.name, "Julia")
        self.assertEqual(package.user_name, "Tony")
        self.assertIn("You are Julia.", prompt.system)
        self.assertIn("speaking with Tony", prompt.system)
        self.assertIn("Private intimacy / relationship contract", prompt.system)
        self.assertNotIn("current_backend", prompt.system)
        self.assertNotIn("deepseek_provider", prompt.system)
        self.assertNotIn("model is only a cognitive provider", prompt.system)

    def test_tc_phase33_019_persona_compiler_applies_context_budget_without_losing_anchors(self):
        context = ContextBuilder(ROOT).build(
            "Julia，刚才那个实验说明了什么？用短句回答。",
            session_id="conv_persona_budget",
            current_backend="deepseek_provider",
        )
        prompt = PromptBuilder().build(context)
        input_chars = sum(len(message["content"]) for message in prompt.to_openai_messages())

        self.assertLess(input_chars, 10000)
        self.assertIn("You are Julia.", prompt.system)
        self.assertIn("speaking with Tony", prompt.system)
        self.assertIn("Conversation contract", prompt.system)
        self.assertIn("Private intimacy / relationship contract", prompt.system)
        self.assertIn("...[trimmed]", prompt.system)


if __name__ == "__main__":
    unittest.main()
