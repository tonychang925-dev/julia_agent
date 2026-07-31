from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.ownership import AudioOwner, AudioOwnershipError, AudioOwnershipManager
from runtime.conversation_runtime.bridge.echo_adapter import EchoAdapter
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import (
    ConversationState,
    ConversationStateMachine,
    InvalidStateTransition,
)


class Phase32StateMachineTests(unittest.TestCase):
    def test_tc_phase32_001_state_machine_rejects_invalid_transition(self):
        sm = ConversationStateMachine()
        with self.assertRaises(InvalidStateTransition) as ctx:
            sm.transition_to(ConversationState.SPEAKING)
        self.assertIn("idle -> speaking", str(ctx.exception))

    def test_tc_phase32_002_echo_turn_flows_listen_to_speak_to_listen(self):
        loop = ConversationLoop(bridge=EchoAdapter())
        result = loop.run_text_turn("你好 Julia")

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
        self.assertEqual(result.turn.user.text, "你好 Julia")
        self.assertEqual(result.turn.assistant.cognitive_backend, "echo_adapter")
        self.assertIn("你好 Tony", result.turn.assistant.text)
        self.assertEqual(result.turn.assistant.metadata["model"], "echo-v0")
        self.assertIn("latency_ms", result.turn.assistant.metadata)

    def test_tc_phase32_003_audio_ownership_user_and_tts_are_exclusive(self):
        manager = AudioOwnershipManager()
        self.assertIs(manager.current_owner, AudioOwner.NONE)

        manager.acquire(AudioOwner.USER)
        self.assertTrue(manager.mic_enabled)
        self.assertFalse(manager.tts_enabled)

        with self.assertRaises(AudioOwnershipError):
            manager.acquire(AudioOwner.TTS)

        manager.release()
        manager.acquire(AudioOwner.TTS)
        self.assertFalse(manager.mic_enabled)
        self.assertTrue(manager.tts_enabled)


if __name__ == "__main__":
    unittest.main()
