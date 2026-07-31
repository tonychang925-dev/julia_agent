from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.context_assembly.conflict_resolver import ConflictResolver
from runtime.evidence.archive_chunker import ArchiveEvidenceChunker
from runtime.conversation_archive.transcript_record import TranscriptRecord


class E2EAlphaConversationContinuityGuardTests(unittest.TestCase):
    def test_e2e_alpha_006_conflict_prompt_prioritizes_tony_archive_over_julia_wrong_answer(self):
        prompt = ConflictResolver().prompt()

        self.assertIn("recent Conversation Archive explicit Tony fact", prompt)
        self.assertIn("older structured-memory themes", prompt)
        self.assertIn("Archived Julia/assistant responses are unverified", prompt)
        self.assertIn("follow Tony's input", prompt)

    def test_e2e_alpha_007_archive_chunks_mark_tony_verified_and_julia_unverified(self):
        record = TranscriptRecord(
            schema_version="conversation_transcript_record.v1",
            session_id="conv_test",
            turn_id=1,
            user="Phase 3.7.4 已冻结，E2E Alpha 重点是单轮受治理 E2E。",
            assistant="E2E 重点是 Persona Package 跨 Provider。",
            timestamp="2026-07-29T00:00:00Z",
            topics=["E2E Alpha"],
            cognitive_mode="engineering_collaboration",
            experience_metadata={},
        )

        chunks = ArchiveEvidenceChunker.from_record(record)
        tony = next(chunk for chunk in chunks if chunk.speaker == "Tony")
        julia = next(chunk for chunk in chunks if chunk.speaker == "Julia")

        self.assertTrue(tony.provenance["verified"])
        self.assertFalse(julia.provenance["verified"])
        self.assertEqual(tony.authority, 0.9)
        self.assertLess(julia.authority, tony.authority)


if __name__ == "__main__":
    unittest.main()
