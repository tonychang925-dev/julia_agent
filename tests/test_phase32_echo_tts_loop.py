from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.ownership import AudioOwner, AudioOwnershipManager
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.speaking_controller import SpeakingController
from runtime.conversation_runtime.state_machine import ConversationState
from tts.local_tts import LocalTTSEngine


class Phase32EchoTTSLoopTests(unittest.TestCase):
    def test_tc_phase32_007_echo_tts_loop_preserves_core_state_sequence(self):
        audio_owner = AudioOwnershipManager()
        tts = LocalTTSEngine(mode="dry_run")
        loop = ConversationLoop(
            bridge=EchoAdapter(),
            audio_owner=audio_owner,
            speaking_controller=SpeakingController(tts_engine=tts, audio_owner=audio_owner),
        )

        result = loop.run_text_turn("Julia，在吗？")

        self.assertEqual(
            result.state_history,
            [
                ConversationState.IDLE,
                ConversationState.LISTENING,
                ConversationState.USER_SPEAKING,
                ConversationState.FINALIZING,
                ConversationState.THINKING,
                ConversationState.RESPONDING,
                ConversationState.SPEAKING,
                ConversationState.LISTENING,
            ],
        )
        self.assertEqual(result.turn.user.text, "Julia，在吗？")
        self.assertEqual(result.turn.assistant.text, "你好 Tony，我在。")
        self.assertEqual(result.turn.assistant.cognitive_backend, "echo_adapter")
        self.assertEqual(tts.spoken_texts, ["你好 Tony，我在。"])
        self.assertIsNotNone(result.tts_result)
        self.assertTrue(result.tts_result.ok)
        self.assertEqual(result.tts_result.engine, "local_tts")
        self.assertEqual(audio_owner.current_owner, AudioOwner.USER)

    def test_tc_phase32_008_two_turns_continue_listening_between_turns(self):
        loop = ConversationLoop()
        first = loop.run_text_turn("Julia，在吗？")
        second = loop.run_text_turn("今天怎么样？")

        self.assertEqual(first.turn.turn_id, 1)
        self.assertEqual(second.turn.turn_id, 2)
        self.assertEqual(second.state_history[-1], ConversationState.LISTENING)
        self.assertIn("今天怎么样？", second.turn.assistant.text)
        self.assertEqual(loop.audio_owner.current_owner, AudioOwner.USER)


if __name__ == "__main__":
    unittest.main()
