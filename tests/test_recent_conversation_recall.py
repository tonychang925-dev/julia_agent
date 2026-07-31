from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.context_assembly.source_memory_resolver import SourceAwareMemoryResolver
from runtime.conversation_archive.transcript_record import TranscriptRecord
from runtime.conversation_archive.transcript_store import TranscriptStore


class RecentConversationRecallTests(unittest.TestCase):
    def test_tc_recent_recall_001_recall_query_injects_tail_archive_before_semantic_memory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = TranscriptStore.default(root)
            store.append(TranscriptRecord(
                schema_version="conversation_transcript_record.v1",
                session_id="previous_session",
                turn_id=7,
                timestamp="2026-07-30T01:00:00+00:00",
                user="Tony asked Julia to debug the dry-run text TTS chat tool.",
                assistant="Julia found that dry_run only prints TTS events and fixed the text-input exit/error behavior.",
                cognitive_mode="engineering_collaboration",
                topics=["dry-run text tts", "bugfix"],
            ))
            resolver = SourceAwareMemoryResolver(root)
            section, meta = resolver._recent_conversation_recall("你还记得上次我们做了什么事情", session_id="current_session")

            self.assertIn("Recent conversation recall", section)
            self.assertIn("dry-run text TTS chat tool", section)
            self.assertIn("fixed the text-input exit/error behavior", section)
            self.assertTrue(meta["triggered"])
            self.assertEqual(meta["hit_count"], 1)
            self.assertEqual(meta["sources"][0]["session_id"], "previous_session")

    def test_tc_recent_recall_002_non_recall_query_does_not_inject_recent_pack(self):
        with tempfile.TemporaryDirectory() as td:
            resolver = SourceAwareMemoryResolver(Path(td))
            section, meta = resolver._recent_conversation_recall("请总结 Phase 3.7.12", session_id="current_session")

            self.assertEqual(section, "")
            self.assertFalse(meta["triggered"])
            self.assertEqual(meta["hit_count"], 0)

    def test_tc_recent_recall_003_current_session_records_are_excluded_from_last_session_recall(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = TranscriptStore.default(root)
            store.append(TranscriptRecord(
                schema_version="conversation_transcript_record.v1",
                session_id="current_session",
                turn_id=1,
                timestamp="2026-07-30T01:00:00+00:00",
                user="current session input",
                assistant="current session output",
            ))
            store.append(TranscriptRecord(
                schema_version="conversation_transcript_record.v1",
                session_id="previous_session",
                turn_id=3,
                timestamp="2026-07-30T00:50:00+00:00",
                user="previous session worked on recent recall bugfix",
                assistant="previous session added chronological recall evidence",
            ))
            resolver = SourceAwareMemoryResolver(root)
            section, meta = resolver._recent_conversation_recall("刚才我们聊了什么内容", session_id="current_session")

            self.assertIn("previous session worked on recent recall bugfix", section)
            self.assertNotIn("current session input", section)
            self.assertEqual(meta["hit_count"], 1)


if __name__ == "__main__":
    unittest.main()
