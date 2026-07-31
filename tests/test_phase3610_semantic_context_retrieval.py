import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import TranscriptRecord, TranscriptStore
from runtime.evidence import (
    ArchiveEvidenceChunker,
    AuthorityAwareSemanticRanker,
    DiaryEvidenceChunker,
    EvidenceAuthority,
    EvidenceChunk,
    EvidenceSourceType,
    EvidenceSpeaker,
    SemanticContextRetriever,
)


class Phase3610SemanticContextRetrievalTests(unittest.TestCase):
    def test_tc_3610_001_diary_heading_chunker_keeps_xiaohongshu_story_together(self):
        with TemporaryDirectory() as td:
            diary = Path(td) / "claude_diary"
            diary.mkdir()
            (diary / "julia_tony_philosophy.md").write_text(
                "# A\nintro\n\n"
                "## Tony's Full Story Revealed\n"
                "Tony shared his Xiaohongshu (小红书) posts.\n"
                "1. 患癌九年\n"
                "2. 爸爸，再见！\n",
                encoding="utf-8",
            )

            chunks = DiaryEvidenceChunker(diary).chunks()
            target = next(chunk for chunk in chunks if "Xiaohongshu" in chunk.content)

            self.assertEqual(target.source_type, EvidenceSourceType.DIARY.value)
            self.assertEqual(target.authority, EvidenceAuthority.CLAUDE_DIARY)
            self.assertIn("患癌九年", target.content)
            self.assertIn("爸爸，再见", target.content)

    def test_tc_3610_002_archive_turn_splits_tony_and_julia_authority(self):
        record = TranscriptRecord(
            schema_version="conversation_transcript_record.v1",
            session_id="s1",
            turn_id=7,
            timestamp="2026-07-28T00:00:00+00:00",
            user="Tony给你看了小红书故事。",
            assistant="我猜故事是错误内容。",
        )

        chunks = ArchiveEvidenceChunker.from_record(record)
        by_speaker = {chunk.speaker: chunk for chunk in chunks}

        self.assertEqual(by_speaker[EvidenceSpeaker.TONY.value].authority, EvidenceAuthority.ARCHIVE_TONY_MESSAGE)
        self.assertEqual(by_speaker[EvidenceSpeaker.JULIA.value].authority, EvidenceAuthority.ARCHIVE_JULIA_MESSAGE)

    def test_tc_3610_003_authority_ranker_prefers_tony_evidence_over_wrong_julia_answer(self):
        chunks = [
            EvidenceChunk(
                id="julia_wrong",
                source_type="archive",
                content="小红书的故事是Julia编出来的错误版本。",
                speaker="Julia",
                authority=0.3,
            ),
            EvidenceChunk(
                id="tony_fact",
                source_type="archive",
                content="Tony给你看了小红书他的故事，这是你们的故事开始。",
                speaker="Tony",
                authority=0.9,
            ),
        ]

        ranked = AuthorityAwareSemanticRanker().rank("小红书的故事", chunks, limit=2)

        self.assertEqual(ranked[0].chunk.id, "tony_fact")
        self.assertGreater(ranked[0].authority, ranked[1].authority)

    def test_tc_3610_004_semantic_retriever_finds_xiaohongshu_without_exact_single_keyword_patch(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            diary = root / "memory" / "claude_diary"
            diary.mkdir(parents=True)
            (diary / "julia_tony_philosophy.md").write_text(
                "## Tony's Full Story Revealed\n"
                "Tony shared his Xiaohongshu (小红书) posts — the most private writings of his life.\n"
                "1. 患癌九年\n"
                "2. 爸爸，再见！\n",
                encoding="utf-8",
            )
            # Required empty memory files are optional; retriever tolerates missing.
            section, metadata = SemanticContextRetriever(root).prompt_section("我给你看过的那些帖子讲了什么", limit=3)

            self.assertTrue(metadata["queried"])
            self.assertGreaterEqual(metadata["hit_count"], 1)
            self.assertIn("Xiaohongshu", section)
            self.assertIn("患癌九年", section)


if __name__ == "__main__":
    unittest.main()
