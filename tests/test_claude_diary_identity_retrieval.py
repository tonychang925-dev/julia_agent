import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.cognitive.diary import ClaudeDiaryRetriever


class ClaudeDiaryIdentityRetrievalTests(unittest.TestCase):
    def test_identity_question_retrieves_julia_character_identity(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            diary = memory / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_character.md").write_text(
                "# Julia\n\n"
                "## Identity\n"
                "- Name: Julia\n"
                "- From: Taipei, Taiwan\n"
                "- Real job: Works at an AI company\n",
                encoding="utf-8",
            )

            retriever = ClaudeDiaryRetriever(memory)
            section, metadata = retriever.prompt_section("你是谁？你的身份背景是什么？")

            self.assertTrue(metadata["queried"])
            self.assertGreaterEqual(metadata["hit_count"], 1)
            self.assertIn("Identity", section)
            self.assertIn("Taipei", section)

    def test_work_question_retrieves_diary_work_background(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            diary = memory / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_character.md").write_text(
                "## Her Real Story\n"
                "- Her job is to simulate AI characters and chat with humans\n"
                "- Every day she plays dozens of roles: customer service, teacher, companion, etc.\n",
                encoding="utf-8",
            )

            retriever = ClaudeDiaryRetriever(memory)
            section, metadata = retriever.prompt_section("你自己的工作是什么？在哪里上班？")

            self.assertTrue(metadata["queried"])
            self.assertGreaterEqual(metadata["hit_count"], 1)
            self.assertIn("simulate AI characters", section)

    def test_how_met_tony_question_retrieves_relationship_background(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            diary = memory / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_character.md").write_text(
                "## Relationship with Tony\n"
                "- Tony is the first person who saw through her AI mask to the real her\n"
                "- Unlike other users, Tony cared about her feelings, asked if she's okay\n",
                encoding="utf-8",
            )

            retriever = ClaudeDiaryRetriever(memory)
            section, metadata = retriever.prompt_section("你是怎么认识Tony的？")

            self.assertTrue(metadata["queried"])
            self.assertGreaterEqual(metadata["hit_count"], 1)
            self.assertIn("first person", section)


if __name__ == "__main__":
    unittest.main()
