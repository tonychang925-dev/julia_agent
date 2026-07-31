from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StartupMemoryGovernanceTests(unittest.TestCase):
    def test_tc_mem_001_startup_identity_loaded_from_governed_facts(self):
        from runtime.memory import StartupMemoryLoader

        pack = StartupMemoryLoader(ROOT).load()

        self.assertTrue(pack.loaded)
        fields = {fact.field: fact.value for fact in pack.facts}
        self.assertEqual(fields["education.university"], "淡江大学")
        self.assertIn("中文", fields["education.major"])
        self.assertIn("朱志豪", fields["family.brother"])
        self.assertIn("没有弟弟", fields["family.sibling_negative"])

    def test_tc_mem_002_fast_greeting_keeps_startup_memory_initialized(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
        from runtime.cognitive.provider.echo_provider import EchoProvider

        bridge = DirectLLMBridge(project_root=ROOT, provider=EchoProvider(), current_backend="echo_provider")
        bridge.send_message("Julia在吗", session_id="startup_greeting", turn_id=1)
        chunks = list(bridge.stream_response(session_id="startup_greeting", turn_id=1))

        self.assertEqual(chunks[0].backend, "short_greeting")
        self.assertTrue(chunks[0].metadata["short_greeting_context_loaded"])
        self.assertTrue(chunks[0].metadata["context_assembly"]["startup_memory"]["loaded"])
        self.assertTrue(chunks[0].metadata["identity_integrity"]["claude_style_memory_loaded"])

    def test_tc_mem_003_governed_fact_beats_quarantined_assistant_archive(self):
        from runtime.evidence import CognitiveEvidenceStore

        chunks = CognitiveEvidenceStore(ROOT).load_all()
        ids = {chunk.id for chunk in chunks}
        contents = "\n".join(chunk.content for chunk in chunks)

        self.assertNotIn("archive:conv_33913d2d975c:2:julia", ids)
        self.assertNotIn("archive:conv_ceed963b3744:7:julia", ids)
        self.assertNotIn("还有一个弟弟", contents)
        self.assertNotIn("台大资工系毕业", contents)

    def test_tc_mem_005_education_multi_slot_coverage_repair(self):
        from runtime.response_quality import AnswerCoverageGate

        gate = AnswerCoverageGate(ROOT)
        result = gate.validate_and_repair("你是哪个大学毕业的，什么专业？", "我是中文系毕业的。")

        self.assertTrue(result.repaired)
        self.assertIn("淡江大学", result.text)
        self.assertIn("中文", result.text)
        self.assertEqual(result.missing_slots, ("education.university",))


if __name__ == "__main__":
    unittest.main()
