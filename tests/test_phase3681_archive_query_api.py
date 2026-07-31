import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import ArchiveQuery, ArchiveQueryEngine, TranscriptStore
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.speaking_controller import SpeakingController
from runtime.runtime_trace import RuntimeEventStore


class Phase3681ArchiveQueryAPITests(unittest.TestCase):
    def make_loop(self, tmp: Path) -> tuple[ConversationLoop, TranscriptStore]:
        store = TranscriptStore(tmp / "transcripts.jsonl")
        loop = ConversationLoop(
            bridge=EchoAdapter(),
            speaking_controller=SpeakingController.dry_run(),
            transcript_store=store,
            runtime_event_store=RuntimeEventStore(tmp / "runtime_events.jsonl"),
        )
        return loop, store

    def test_archive_query_filters_by_experience_type_and_text(self):
        with TemporaryDirectory() as td:
            loop, store = self.make_loop(Path(td))
            loop.run_text_turn("我们冻结ADR路线。")
            loop.run_text_turn("今天天气不错。")

            result = ArchiveQueryEngine(store).query(ArchiveQuery(text_contains="ADR", experience_type="decision", limit=10))

            self.assertEqual(result.count, 1)
            self.assertIn("ADR", result.records[0].user)
            self.assertEqual(result.total_scanned, 2)

    def test_archive_query_returns_latest_reflection_candidates(self):
        with TemporaryDirectory() as td:
            loop, store = self.make_loop(Path(td))
            loop.run_text_turn("你好。")
            loop.run_text_turn("Tony和Julia完成了重要里程碑。")

            result = ArchiveQueryEngine(store).latest_reflection_candidates(limit=5)

            self.assertEqual(result.count, 1)
            self.assertIn("里程碑", result.records[0].user)
