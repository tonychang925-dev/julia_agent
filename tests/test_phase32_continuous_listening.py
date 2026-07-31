from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.buffer import make_energy_frames
from audio.ownership import AudioOwner
from audio.vad_engine import VADConfig, VADEngine
from runtime.conversation_runtime.listening_loop import ContinuousListeningLoop
from runtime.conversation_runtime.state_machine import ConversationState
from stt.finalizer import MockSTTFinalizer


class Phase32ContinuousListeningTests(unittest.TestCase):
    def test_tc_phase32_004_vad_finalizes_after_silence_timeout(self):
        # 500ms idle, 600ms speech, 1200ms silence at 100ms/frame.
        frames = make_energy_frames([0.01] * 5 + [0.20] * 6 + [0.01] * 12)
        loop = ContinuousListeningLoop(
            vad=VADEngine(VADConfig(initial_noise_floor=0.02, silence_timeout_ms=1200, min_speech_ms=300)),
            stt_finalizer=MockSTTFinalizer("Julia，在吗？"),
        )

        result = loop.run_frames(frames)

        self.assertEqual(result.finalized_texts, ["Julia，在吗？"])
        self.assertEqual(
            result.state_history,
            [
                ConversationState.IDLE,
                ConversationState.LISTENING,
                ConversationState.USER_SPEAKING,
                ConversationState.FINALIZING,
                ConversationState.LISTENING,
            ],
        )
        self.assertIn("Julia Voice Runtime started", result.event_log)
        self.assertIn("state=USER_SPEAKING", result.event_log)
        self.assertIn("finalizing...", result.event_log)
        self.assertEqual(loop.audio_owner.current_owner, AudioOwner.USER)

    def test_tc_phase32_005_short_noise_does_not_submit_empty_text(self):
        # 100ms spike is below min_speech_ms, followed by enough silence to discard.
        frames = make_energy_frames([0.01] * 5 + [0.20] + [0.01] * 12)
        loop = ContinuousListeningLoop(
            vad=VADEngine(VADConfig(initial_noise_floor=0.02, silence_timeout_ms=1200, min_speech_ms=300)),
            stt_finalizer=MockSTTFinalizer("SHOULD_NOT_SUBMIT"),
        )

        result = loop.run_frames(frames)

        self.assertEqual(result.finalized_texts, [])
        self.assertIn("discarded_segment reason=min_speech_ms", result.event_log)
        self.assertEqual(result.state_history[-1], ConversationState.LISTENING)


if __name__ == "__main__":
    unittest.main()
