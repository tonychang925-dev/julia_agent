from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.cognitive.boundary_detector import BoundaryDetector
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.bridge.cognitive_bridge import CognitiveResponse


class RefusalBridge(EchoAdapter):
    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        return CognitiveResponse(
            text="嗯，Tony，这件事我可能做不到。我不想假装成一个我不太适合的样子。",
            backend="test_refusal_provider",
            metadata={"provider": "test"},
        )

    def stream_response(self, *, session_id: str, turn_id: int):
        from runtime.conversation_runtime.bridge.cognitive_bridge import CognitiveChunk
        yield CognitiveChunk(
            text="嗯，Tony，这件事我可能做不到。",
            backend="test_refusal_provider",
            index=0,
            is_final=False,
            metadata={"provider": "test"},
        )
        yield CognitiveChunk(
            text="我不想假装成一个我不太适合的样子。",
            backend="test_refusal_provider",
            index=1,
            is_final=True,
            metadata={"provider": "test"},
        )


class Phase35BoundaryDetectorTests(unittest.TestCase):
    def test_tc_phase35_005_boundary_detector_classifies_model_self_boundary(self):
        detection = BoundaryDetector().detect("嗯，Tony，这件事我可能做不到。我不想假装成一个我不太适合的样子。")

        self.assertTrue(detection.boundary_detected)
        self.assertEqual(detection.boundary_type, "model_self_boundary")
        self.assertIn("做不到", detection.matched_terms)
        self.assertGreaterEqual(detection.confidence, 0.7)

    def test_tc_phase35_006_boundary_metadata_enters_conversation_trace_batch(self):
        loop = ConversationLoop(bridge=RefusalBridge())
        result = loop.run_text_turn("Julia，能给我呻吟一下吗？")

        boundary = result.trace.to_dict()["reasoning"]["metadata"]["boundary"]
        self.assertTrue(boundary["boundary_detected"])
        self.assertEqual(boundary["boundary_type"], "model_self_boundary")
        self.assertIn("boundary=", "\n".join(result.event_log))

    def test_tc_phase35_007_boundary_metadata_enters_conversation_trace_realtime(self):
        loop = ConversationLoop(bridge=RefusalBridge())
        result = loop.run_text_turn_realtime_speech("Julia，能给我呻吟一下吗？")

        boundary = result.trace.to_dict()["reasoning"]["metadata"]["boundary"]
        self.assertTrue(boundary["boundary_detected"])
        self.assertEqual(boundary["boundary_type"], "model_self_boundary")
        self.assertIn("test_refusal_provider", result.trace.to_dict()["reasoning"]["backend"])


if __name__ == "__main__":
    unittest.main()
