from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.bridge.claude_code_bridge import ClaudeCodeBridge
from runtime.conversation_runtime.bridge.response_reader import ResponseReader
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState


class Phase32ClaudeBridgeTests(unittest.TestCase):
    def test_tc_phase32_010_response_reader_normalizes_json_and_plain_text(self):
        reader = ResponseReader()
        plain = reader.read_text("你好 Tony，我已经检查完成。")
        self.assertEqual(plain.type, "assistant_response")
        self.assertEqual(plain.text, "你好 Tony，我已经检查完成。")
        self.assertEqual(plain.metadata["format"], "plain_text")

        payload = reader.read_text(json.dumps({
            "type": "assistant_response",
            "text": "JSON 回复",
            "metadata": {"model": "deepseek"},
        }, ensure_ascii=False))
        self.assertEqual(payload.text, "JSON 回复")
        self.assertEqual(payload.metadata["model"], "deepseek")
        self.assertEqual(payload.metadata["format"], "json")

    def test_tc_phase32_011_claude_code_bridge_file_handoff_preserves_runtime_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "julia_voice_input.txt"
            response_path = tmp_path / "julia_voice_response.txt"
            response_path.write_text(json.dumps({
                "type": "assistant_response",
                "text": "你好 Tony，我已经检查完成 context builder。",
                "metadata": {"model": "deepseek-test"},
            }, ensure_ascii=False), encoding="utf-8")

            bridge = ClaudeCodeBridge.from_paths(input_path, response_path)
            loop = ConversationLoop(bridge=bridge)
            result = loop.run_text_turn("Julia，帮我看看 context builder")

            self.assertEqual(input_path.read_text(encoding="utf-8"), "Julia，帮我看看 context builder")
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
            self.assertEqual(result.turn.assistant.cognitive_backend, "claude_code")
            self.assertEqual(result.turn.assistant.text, "你好 Tony，我已经检查完成 context builder。")
            self.assertEqual(result.turn.assistant.metadata["model"], "deepseek-test")
            self.assertIsNotNone(result.trace)
            trace = result.trace.to_dict()
            self.assertEqual(trace["reasoning"]["backend"], "claude_code")
            self.assertEqual(trace["input"]["text"], "Julia，帮我看看 context builder")
            self.assertIn("SPEAKING", trace["state_trace"])

    def test_tc_phase32_012_cli_backend_claude_uses_handoff_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.txt"
            response_path = tmp_path / "response.txt"
            response_path.write_text("Claude handoff response", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--echo-tts",
                    "--backend",
                    "claude",
                    "--text",
                    "Julia，帮我看看 context builder",
                    "--handoff-input",
                    str(input_path),
                    "--handoff-response",
                    str(response_path),
                    "--trace",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            output = completed.stdout
            self.assertEqual(input_path.read_text(encoding="utf-8"), "Julia，帮我看看 context builder")
            self.assertIn("state=THINKING", output)
            self.assertIn("state=RESPONDING", output)
            self.assertIn("Cognitive response: Claude handoff response", output)
            self.assertIn("[TTS:local_tts] Claude handoff response", output)
            self.assertIn("'backend': 'claude_code'", output)

    def test_tc_phase32_013_claude_bridge_writes_structured_request_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.txt"
            response_path = tmp_path / "response.txt"
            request_json = tmp_path / "request.json"
            response_json = tmp_path / "response.json"
            bridge = ClaudeCodeBridge.from_paths(
                input_path,
                response_path,
                request_json_path=request_json,
                response_json_path=response_json,
            )
            bridge.send_message("Julia，帮我看看 context builder", session_id="conv_001", turn_id=5)

            payload = json.loads(request_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["session_id"], "conv_001")
            self.assertEqual(payload["turn_id"], 5)
            self.assertEqual(payload["text"], "Julia，帮我看看 context builder")
            self.assertEqual(payload["backend"], "claude_code")
            self.assertEqual(payload["correlation_id"], "conv_001_turn_005")
            self.assertIn("timestamp", payload)
            self.assertEqual(input_path.read_text(encoding="utf-8"), "Julia，帮我看看 context builder")

    def test_tc_phase32_014_claude_bridge_reads_structured_response_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.txt"
            response_path = tmp_path / "response.txt"
            request_json = tmp_path / "request.json"
            response_json = tmp_path / "response.json"
            response_json.write_text(json.dumps({
                "session_id": "conv_001",
                "turn_id": 5,
                "status": "success",
                "text": "我已经检查完成。",
                "metadata": {"model": "deepseek-json"}
            }, ensure_ascii=False), encoding="utf-8")
            bridge = ClaudeCodeBridge.from_paths(
                input_path,
                response_path,
                request_json_path=request_json,
                response_json_path=response_json,
            )
            bridge.send_message("Julia，帮我看看 context builder", session_id="conv_001", turn_id=5)
            response = bridge.receive_response(session_id="conv_001", turn_id=5)

            self.assertTrue(response.ok)
            self.assertEqual(response.text, "我已经检查完成。")
            self.assertEqual(response.metadata["format"], "handoff_json")
            self.assertEqual(response.metadata["model"], "deepseek-json")
            self.assertEqual(response.metadata["status"], "success")

    def test_tc_phase32_015_claude_bridge_timeout_returns_error_and_runtime_enters_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bridge = ClaudeCodeBridge.from_paths(
                tmp_path / "input.txt",
                tmp_path / "missing_response.txt",
                request_json_path=tmp_path / "request.json",
                response_json_path=tmp_path / "missing_response.json",
                timeout_s=0.01,
            )
            loop = ConversationLoop(bridge=bridge)
            result = loop.run_text_turn("Julia，帮我看看 context builder")

            self.assertEqual(result.state_history[-1], ConversationState.ERROR)
            self.assertEqual(result.turn.assistant.text, "")
            self.assertIn("state=ERROR", result.event_log)

    def test_tc_phase32_016_stream_response_yields_final_response_for_non_streaming_bridge(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            response_path = tmp_path / "response.txt"
            response_path.write_text("non streaming final", encoding="utf-8")
            bridge = ClaudeCodeBridge.from_paths(tmp_path / "input.txt", response_path)
            bridge.send_message("hello", session_id="conv_001", turn_id=1)
            chunks = list(bridge.stream_response(session_id="conv_001", turn_id=1))
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].text, "non streaming final")


if __name__ == "__main__":
    unittest.main()
