import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import TranscriptStore
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.speaking_controller import SpeakingController


class Phase368ConversationExperienceArchiveTests(unittest.TestCase):
    def test_transcript_store_appends_completed_turn_as_jsonl_experience_record(self):
        with TemporaryDirectory() as td:
            archive_path = Path(td) / "transcripts.jsonl"
            loop = ConversationLoop(
                bridge=EchoAdapter(),
                speaking_controller=SpeakingController.dry_run(),
                transcript_store=TranscriptStore(archive_path),
            )

            result = loop.run_text_turn("Julia你是谁？")

            self.assertTrue(archive_path.exists())
            line = archive_path.read_text(encoding="utf-8").strip()
            data = json.loads(line)
            self.assertEqual(data["schema_version"], "conversation_transcript_record.v1")
            self.assertEqual(data["session_id"], result.turn.session_id)
            self.assertEqual(data["turn_id"], 1)
            self.assertEqual(data["user"], "Julia你是谁？")
            self.assertIn("Julia你是谁？", data["assistant"])
            self.assertEqual(data["provenance"]["archive_role"], "experience_archive_not_prompt_injection")

    def test_transcript_store_tail_reads_recent_records(self):
        with TemporaryDirectory() as td:
            store = TranscriptStore(Path(td) / "transcripts.jsonl")
            loop = ConversationLoop(bridge=EchoAdapter(), speaking_controller=SpeakingController.dry_run(), transcript_store=store)
            loop.run_text_turn("第一句。")
            loop.run_text_turn("第二句。")

            records = store.tail(1)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].user, "第二句。")
