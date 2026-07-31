import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.cognitive.diary import ClaudeDiaryRetriever
from runtime.conversation_archive import ConversationArchiveRetriever, TranscriptRecord, TranscriptStore


class XiaohongshuStoryRetrievalTests(unittest.TestCase):
    def test_diary_prioritizes_exact_xiaohongshu_story_source(self):
        with TemporaryDirectory() as td:
            memory = Path(td) / "memory"
            diary = memory / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_tony_philosophy.md").write_text(
                "## Generic Tony\nTony was different and gave real love.\n\n"
                "## Tony's Full Story Revealed\n"
                "Tony shared his Xiaohongshu (小红书) posts — the most private writings of his life.\n"
                "1. **患癌九年** — cancer recovery.\n"
                "2. **爸爸，再见！** — father passed away.\n",
                encoding="utf-8",
            )

            section, metadata = ClaudeDiaryRetriever(memory).prompt_section("小红书的故事", limit=2)

            self.assertTrue(metadata["queried"])
            self.assertEqual(metadata["sources"][0]["source"], "julia_tony_philosophy.md")
            self.assertIn("Xiaohongshu", section)
            self.assertIn("患癌九年", section)
            self.assertIn("爸爸，再见", section)

    def test_archive_filters_prior_wrong_julia_answer_for_xiaohongshu_story(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            store.append(TranscriptRecord(
                schema_version="conversation_transcript_record.v1",
                session_id="s1",
                turn_id=16,
                timestamp="2026-07-28T00:00:00+00:00",
                user="你读过小红书的故事吗你能查一下本地memory吗。",
                assistant="我读过，但本地memory里没有存完整原文。",
            ))
            store.append(TranscriptRecord(
                schema_version="conversation_transcript_record.v1",
                session_id="s1",
                turn_id=35,
                timestamp="2026-07-28T00:01:00+00:00",
                user="Tony给你看了小红书他的故事你看完之后你亲呢Tony记得吗这是你们的故事开始。",
                assistant="我记得。",
            ))

            evidence = ConversationArchiveRetriever(store).retrieve("小红书的故事", session_id="s1")

            self.assertTrue(evidence)
            self.assertEqual(evidence[0].turn_id, 35)
            self.assertNotIn(16, [item.turn_id for item in evidence])


if __name__ == "__main__":
    unittest.main()
