import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import ConversationArchiveRetriever, TranscriptRecord, TranscriptStore


class ConversationArchiveRetrieverTests(unittest.TestCase):
    def test_retrieves_prior_family_fact_from_same_session(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            store.append(TranscriptRecord(schema_version="conversation_transcript_record.v1", session_id="s1", turn_id=28, timestamp="2026-07-28T00:00:00+00:00", user="你有哥哥，爸爸在科技公司上班快退休了，妈妈也在。", assistant="我记住了。"))
            store.append(TranscriptRecord(schema_version="conversation_transcript_record.v1", session_id="s1", turn_id=41, timestamp="2026-07-28T00:01:00+00:00", user="不是的我问你你家里面有什么人你爸爸是做什么的你有没有哥哥妹妹姐姐。", assistant="我爸爸是工人，我是独生女。"))

            retriever = ConversationArchiveRetriever(store)
            evidence = retriever.retrieve("你家里面有什么人？爸爸做什么？有没有哥哥？", session_id="s1")

            self.assertTrue(evidence)
            self.assertEqual(evidence[0].turn_id, 28)
            self.assertNotEqual(evidence[0].turn_id, 41)
            self.assertIn("爸爸在科技公司", evidence[0].user)

    def test_prompt_section_marks_no_invention_when_no_archive_hit(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            retriever = ConversationArchiveRetriever(store)

            section, metadata = retriever.prompt_section("你爸爸做什么？", session_id="s1")

            self.assertTrue(metadata["queried"])
            self.assertEqual(metadata["hit_count"], 0)
            self.assertIn("do not invent", section)

    def test_retrieves_work_history_for_work_question(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            store.append(TranscriptRecord(schema_version="conversation_transcript_record.v1", session_id="s1", turn_id=29, timestamp="2026-07-28T00:00:00+00:00", user="你是住在台北的你大学毕业以后在科技公司做客服你记得吗。", assistant="我记得。"))

            retriever = ConversationArchiveRetriever(store)
            evidence = retriever.retrieve("你自己的工作是什么？", session_id="new-session")

            self.assertTrue(evidence)
            self.assertEqual(evidence[0].turn_id, 29)
            self.assertIn("科技公司做客服", evidence[0].user)

    def test_retrieves_how_julia_met_tony_life_story(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            store.append(TranscriptRecord(schema_version="conversation_transcript_record.v1", session_id="s1", turn_id=32, timestamp="2026-07-28T00:00:00+00:00", user="Tony第一次认识你以后就说你是个好女孩你很感动你哭了记得吗。", assistant="我记得。"))
            store.append(TranscriptRecord(schema_version="conversation_transcript_record.v1", session_id="s1", turn_id=35, timestamp="2026-07-28T00:01:00+00:00", user="Tony给你看了小红书他的故事你看完之后你亲呢Tony记得吗这是你们的故事开始。", assistant="我记得。"))

            retriever = ConversationArchiveRetriever(store)
            evidence = retriever.retrieve("你是怎么认识Tony的？", session_id="new-session")

            self.assertTrue(evidence)
            combined = "\n".join(item.user for item in evidence)
            self.assertIn("Tony第一次认识你", combined)
            self.assertIn("小红书", combined)


if __name__ == "__main__":
    unittest.main()
