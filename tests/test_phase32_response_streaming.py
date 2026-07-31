from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.ownership import AudioOwner
from runtime.conversation_runtime.bridge.claude_code_bridge import ClaudeCodeBridge
from runtime.conversation_runtime.bridge.echo_bridge import EchoBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState
from tts.local_tts import LocalTTSEngine


class Phase32ResponseStreamingTests(unittest.TestCase):
    def test_tc_phase32_017_echo_streaming_preserves_runtime_state_sequence(self):
        loop = ConversationLoop(bridge=EchoBridge())
        result = loop.run_text_turn_streaming("Julia，在吗？")

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
        self.assertEqual(result.turn.assistant.text, "你好 Tony，我在。")
        self.assertEqual(result.turn.assistant.cognitive_backend, "echo_adapter")
        self.assertEqual(result.turn.assistant.metadata["streaming"], True)
        self.assertIn("Response chunk[0]", "\n".join(result.event_log))
        self.assertEqual(loop.audio_owner.current_owner, AudioOwner.USER)

    def test_tc_phase32_018_claude_stream_jsonl_chunks_feed_tts_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            stream_path = tmp_path / "response.stream.jsonl"
            session_id = "conv_stream"
            lines = [
                {"type": "response_chunk", "session_id": session_id, "turn_id": 1, "text": "Tony，我先看一下。", "is_final": False},
                {"type": "response_chunk", "session_id": session_id, "turn_id": 1, "text": "context builder 的结构是清晰的。", "is_final": True},
            ]
            stream_path.write_text("\n".join(json.dumps(line, ensure_ascii=False) for line in lines), encoding="utf-8")
            bridge = ClaudeCodeBridge.from_paths(
                tmp_path / "input.txt",
                tmp_path / "response.txt",
                request_json_path=tmp_path / "request.json",
                response_json_path=tmp_path / "response.json",
                stream_jsonl_path=stream_path,
            )
            loop = ConversationLoop(bridge=bridge)
            loop.session.session_id = session_id
            loop.turn_manager.session_id = session_id

            result = loop.run_text_turn_streaming("Julia，帮我分析一下 context builder")

            self.assertEqual(result.turn.assistant.cognitive_backend, "claude_code")
            self.assertEqual(result.turn.assistant.text, "Tony，我先看一下。context builder 的结构是清晰的。")
            self.assertIn("Response chunk[0]: Tony，我先看一下。", result.event_log)
            self.assertIn("Response chunk[1]: context builder 的结构是清晰的。", result.event_log)
            self.assertIn("[TTS_CHUNK:0:local_tts] Tony，我先看一下。context builder 的结构是清晰的。", result.event_log)
            request = json.loads((tmp_path / "request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["text"], "Julia，帮我分析一下 context builder")

    def test_tc_phase32_019_cli_stream_echo_prints_chunks(self):
        completed = subprocess.run(
            [sys.executable, "-m", "runtime.conversation_runtime.cli", "--echo-tts", "--stream", "--backend", "echo", "--text", "Julia，在吗？"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("state=THINKING", output)
        self.assertIn("state=RESPONDING", output)
        self.assertIn("Response chunk[0]", output)
        self.assertIn("state=SPEAKING", output)
        self.assertIn("[TTS_CHUNK:0:local_tts]", output)
        self.assertIn("state=LISTENING", output)
        self.assertIn("latency=", output)


if __name__ == "__main__":
    unittest.main()
