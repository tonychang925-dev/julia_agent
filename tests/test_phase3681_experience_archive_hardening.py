import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.conversation_archive import TranscriptStore, ExperienceClassifier
from runtime.runtime_trace import RuntimeEventStore
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.speaking_controller import SpeakingController


class Phase3681ExperienceArchiveHardeningTests(unittest.TestCase):
    def test_experience_archive_excludes_runtime_backend_audio_and_latency(self):
        with TemporaryDirectory() as td:
            archive_path = Path(td) / "transcripts.jsonl"
            runtime_path = Path(td) / "runtime_events.jsonl"
            loop = ConversationLoop(
                bridge=EchoAdapter(),
                speaking_controller=SpeakingController.dry_run(),
                transcript_store=TranscriptStore(archive_path),
                runtime_event_store=RuntimeEventStore(runtime_path),
            )

            loop.run_text_turn("我们应该冻结ADR结论。")

            experience = json.loads(archive_path.read_text(encoding="utf-8").strip())
            runtime = json.loads(runtime_path.read_text(encoding="utf-8").strip())
            self.assertNotIn("backend", experience)
            self.assertNotIn("audio", experience)
            self.assertNotIn("latency", experience)
            self.assertIn("experience_metadata", experience)
            self.assertEqual(runtime["backend"], "echo_adapter")
            self.assertIn("audio", runtime)
            self.assertIn("latency", runtime)

    def test_experience_classifier_marks_decision_and_technical_turns(self):
        meta = ExperienceClassifier().classify(
            user="我建议冻结ADR路线。",
            assistant="同意，我们冻结Julia Runtime的Context Engineering路线。",
            cognitive_mode="engineering_collaboration",
            topics=["Julia Runtime", "Context Engineering"],
        )

        self.assertIn("technical", meta.experience_type)
        self.assertIn("decision", meta.experience_type)
        self.assertTrue(meta.reflection_candidate)
        self.assertGreater(meta.importance_hint.project, 0)
