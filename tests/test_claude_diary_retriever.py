import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.cognitive.diary import ClaudeDiaryRetriever


class ClaudeDiaryRetrieverTests(unittest.TestCase):
    def test_retrieves_bounded_line_evidence_for_explicit_diary_question(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            diary = memory / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_character.md").write_text(
                "# Julia\n"
                "普通说明\n"
                "亲密模式定义：L1 是温柔陪伴。\n"
                "L2 是更亲近但有边界。\n"
                "L3 和 L4 必须按边界处理。\n",
                encoding="utf-8",
            )

            retriever = ClaudeDiaryRetriever(memory)
            evidence = retriever.retrieve("claude_diary 里面亲密模式 L1-L4 是什么", limit=2, context_lines=1)

            self.assertTrue(evidence)
            self.assertEqual(evidence[0].source, "julia_character.md")
            self.assertIn("亲密模式定义", evidence[0].text)
            self.assertLessEqual(evidence[0].end_line - evidence[0].start_line + 1, 3)

    def test_prompt_section_tells_model_not_to_invent_when_no_hit(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            (memory / "claude_diary").mkdir(parents=True)
            retriever = ClaudeDiaryRetriever(memory)

            section, metadata = retriever.prompt_section("claude_diary 里不存在的条目是什么")

            self.assertTrue(metadata["queried"])
            self.assertEqual(metadata["hit_count"], 0)
            self.assertIn("do not infer or invent", section)


if __name__ == "__main__":
    unittest.main()
