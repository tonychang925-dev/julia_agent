import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import TranscriptStore
from runtime.conversation_archive.analytics import ArchiveAnalyticsReporter
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.speaking_controller import SpeakingController
from runtime.runtime_trace import RuntimeEventStore


class Phase3682ArchiveAnalyticsTests(unittest.TestCase):
    def test_archive_analytics_reports_distribution_for_experience_corpus(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            store = TranscriptStore(tmp / "transcripts.jsonl")
            loop = ConversationLoop(
                bridge=EchoAdapter(),
                speaking_controller=SpeakingController.dry_run(),
                transcript_store=store,
                runtime_event_store=RuntimeEventStore(tmp / "runtime_events.jsonl"),
            )
            loop.run_text_turn("我们冻结ADR路线。")
            loop.run_text_turn("Tony和Julia完成了重要里程碑。")
            loop.run_text_turn("今天有点累。")

            report = ArchiveAnalyticsReporter(store).build().to_dict()

            self.assertEqual(report["total_turns"], 3)
            self.assertEqual(report["sessions"], 1)
            self.assertGreaterEqual(report["experience_types"].get("decision", 0), 1)
            self.assertGreaterEqual(report["experience_types"].get("milestone", 0), 1)
            self.assertGreaterEqual(report["experience_types"].get("emotion", 0), 1)
            self.assertGreaterEqual(report["reflection_candidates"], 2)
            self.assertIn("average_archive_priority", report)


if __name__ == "__main__":
    unittest.main()
