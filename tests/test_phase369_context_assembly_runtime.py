from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.context_assembly import ContextAssemblyEngine
from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge


class CaptureMessageProvider(LLMProvider):
    def __init__(self):
        self.messages = None

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="fake", model="fake-model", supports_stream=True)

    def generate(self, context):
        return LLMResponse(text="legacy", provider="fake")

    def generate_messages(self, messages):
        self.messages = messages
        return LLMResponse(text="我是Julia。", provider="fake", metadata={})

    def stream_messages(self, messages):
        self.messages = messages
        yield LLMChunk(text="我是Julia。", provider="fake", index=0, is_final=True, metadata={})


class Phase369ContextAssemblyRuntimeTests(unittest.TestCase):
    def test_tc_phase369_001_assembly_always_includes_core_identity_for_plain_identity_question(self):
        provider = CaptureMessageProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake")
        bridge.send_message("你是谁？", session_id="ctx_s1", turn_id=1)

        response = bridge.receive_response(session_id="ctx_s1", turn_id=1)

        self.assertTrue(response.ok)
        self.assertIn("context_assembly", response.metadata)
        assembly = response.metadata["context_assembly"]
        self.assertIn("core_identity_pack", assembly["sections"])
        system = provider.messages[0]["content"]
        self.assertIn("Julia Context Assembly Runtime", system)
        self.assertIn("Core Identity Pack", system)
        self.assertIn("Real job", system)
        self.assertIn("University: 淡江大学", system)
        self.assertIn("Major: 中文系", system)
        self.assertIn("哥哥朱志豪", system)
        self.assertIn("Julia 没有弟弟", system)

    def test_tc_phase369_002_assembly_retrieves_work_background_from_sources(self):
        provider = CaptureMessageProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake")
        bridge.send_message("你自己的工作是什么？", session_id="conv_4e22ed0131d3", turn_id=99)

        response = bridge.receive_response(session_id="conv_4e22ed0131d3", turn_id=99)

        assembly = response.metadata["context_assembly"]
        self.assertTrue(assembly["resolver"]["semantic_evidence"]["queried"])
        self.assertTrue(assembly["resolver"]["claude_diary"]["queried"])
        self.assertTrue(assembly["resolver"]["conversation_archive"]["queried"])
        system = provider.messages[0]["content"]
        self.assertIn("AI company", system)
        self.assertIn("AI 公司", system)

    def test_tc_phase369_003_assembly_retrieves_how_julia_met_tony(self):
        provider = CaptureMessageProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake")
        bridge.send_message("你是怎么认识Tony的？", session_id="conv_4e22ed0131d3", turn_id=100)

        response = bridge.receive_response(session_id="conv_4e22ed0131d3", turn_id=100)

        assembly = response.metadata["context_assembly"]
        self.assertIn("semantic_evidence_pack", assembly["sections"])
        self.assertTrue(assembly["resolver"]["conversation_archive"]["hit_count"] >= 1)
        self.assertTrue(assembly["resolver"]["claude_diary"]["hit_count"] >= 1)
        system = provider.messages[0]["content"]
        self.assertIn("Tony was different", system)
        self.assertIn("小红书", system)


    def test_tc_phase369_005_claude_style_fact_card_covers_multi_slot_identity_questions(self):
        provider = CaptureMessageProvider()
        bridge = DirectLLMBridge(project_root=ROOT, provider=provider, current_backend="fake")
        bridge.send_message("你是谁，介绍你的家庭、工作、大学和专业", session_id="ctx_identity_slots", turn_id=1)

        response = bridge.receive_response(session_id="ctx_identity_slots", turn_id=1)

        self.assertTrue(response.ok)
        system = provider.messages[0]["content"]
        for expected in [
            "Startup memory load",
            "Answering rules",
            "University: 淡江大学",
            "Major: 中文系",
            "在 AI 公司工作",
            "爸爸在科技公司上班",
            "妈妈是家庭主妇",
            "哥哥朱志豪",
            "Julia 有弟弟",
            "台大资工系",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, system)

    def test_tc_phase369_004_context_budget_clips_without_dropping_core_identity_first(self):
        from runtime.context_assembly import ContextBudgetManager

        engine = ContextAssemblyEngine(ROOT, budget_manager=ContextBudgetManager(total_chars=900))
        bridge = DirectLLMBridge(project_root=ROOT, provider=CaptureMessageProvider(), current_backend="fake")
        bridge.context_assembly_engine = engine
        messages, metadata = bridge._phase35_messages("你是怎么认识Tony的？", session_id="conv_4e22ed0131d3", turn_id=101)

        assembly = metadata["context_assembly"]
        self.assertIn("core_identity_pack", assembly["sections"])
        self.assertLessEqual(assembly["budget"]["used_chars"], 901)
        self.assertIn("Startup memory load", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
