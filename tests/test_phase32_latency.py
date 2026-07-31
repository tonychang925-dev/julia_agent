from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.latency import LatencyTracker


class Phase32LatencyTests(unittest.TestCase):
    def test_tc_phase32_020_latency_tracker_reports_ttfv_metrics_and_targets(self):
        tracker = LatencyTracker()
        tracker.start_turn(12)
        tracker.mark_speech_end()
        tracker.mark_stt_final()
        tracker.mark_bridge_request()
        tracker.mark_first_chunk()
        tracker.mark_tts_start()
        snapshot = tracker.finish()
        payload = snapshot.to_dict()

        self.assertEqual(payload["turn_id"], 12)
        self.assertIn("speech_to_text_ms", payload["latency"])
        self.assertIn("bridge_first_chunk_ms", payload["latency"])
        self.assertIn("tts_start_ms", payload["latency"])
        self.assertIn("time_to_first_voice_ms", payload["latency"])
        self.assertIn("total_response_ms", payload["latency"])
        self.assertEqual(payload["targets"]["time_to_first_voice_ms"], 2500)
        self.assertIsNotNone(payload["passed"]["time_to_first_voice_ms"])

    def test_tc_phase32_021_conversation_trace_contains_latency_snapshot(self):
        loop = ConversationLoop()
        result = loop.run_text_turn_streaming("Julia，在吗？")

        self.assertIsNotNone(result.latency)
        self.assertIsNotNone(result.trace)
        trace = result.trace.to_dict()
        self.assertIn("latency", trace)
        self.assertEqual(trace["latency"]["turn_id"], 1)
        self.assertIn("time_to_first_voice_ms", trace["latency"]["latency"])
        self.assertIn("latency=", "\n".join(result.event_log))


if __name__ == "__main__":
    unittest.main()
