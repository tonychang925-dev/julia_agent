from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase37ShortGreetingTests(unittest.TestCase):
    def test_tc_phase37_001_short_greeting_matcher(self):
        from runtime.cognitive.short_greeting import ShortGreetingResponder

        responder = ShortGreetingResponder()
        for text in ["Julia你在吗。", "Julia，在吗？", "Julia你在不在", "你在吗。"]:
            with self.subTest(text=text):
                result = responder.match(text)
                self.assertTrue(result.matched)
                self.assertEqual(result.text, "嗯，Tony，我在。")

    def test_tc_phase37_002_direct_llm_bridge_short_circuits_provider_for_greeting(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
        from runtime.cognitive.provider.echo_provider import EchoProvider

        bridge = DirectLLMBridge(project_root=ROOT, provider=EchoProvider(), current_backend="echo_provider")
        bridge.send_message("Julia你在吗。", session_id="s", turn_id=1)
        chunks = list(bridge.stream_response(session_id="s", turn_id=1))

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "嗯，Tony，我在。")
        self.assertEqual(chunks[0].backend, "short_greeting")
        self.assertEqual(chunks[0].metadata["provider"], "local_short_greeting")
        self.assertTrue(chunks[0].metadata["short_greeting_context_loaded"])
        self.assertTrue(chunks[0].metadata["identity_integrity"]["claude_style_memory_loaded"])
        self.assertIn("core_identity_pack", chunks[0].metadata["context_assembly"]["sections"])

    def test_tc_phase37_003_short_greeting_can_be_disabled(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
        from runtime.cognitive.provider.echo_provider import EchoProvider

        bridge = DirectLLMBridge(
            project_root=ROOT,
            provider=EchoProvider(),
            current_backend="echo_provider",
            short_greeting_enabled=False,
        )
        bridge.send_message("Julia你在吗。", session_id="s", turn_id=1)
        chunks = list(bridge.stream_response(session_id="s", turn_id=1))

        self.assertNotEqual(chunks[0].backend, "short_greeting")
        self.assertIn("Julia", "".join(chunk.text for chunk in chunks))

    def test_tc_phase37_004_cli_short_greeting_uses_local_backend_without_deepseek_key(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--backend",
                "deepseek",
                "--stream",
                "--realtime-speech",
                "--text",
                "Julia你在吗。",
                "--trace",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("Response chunk[0]: 嗯，Tony，我在。", completed.stdout)
        self.assertIn("'backend': 'short_greeting'", completed.stdout)
        self.assertIn("local_short_greeting", completed.stdout)
        self.assertIn("'short_greeting_context_loaded': True", completed.stdout)
        self.assertIn("'claude_style_memory_loaded': True", completed.stdout)


    def test_tc_phase37_005_cli_skips_fast_ack_for_short_greeting(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--backend",
                "deepseek",
                "--stream",
                "--realtime-speech",
                "--text",
                "Julia你在吗。",
                "--trace",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("Response chunk[0]: 嗯，Tony，我在。", completed.stdout)
        self.assertNotIn("[TTS_ACK", completed.stdout)
        self.assertIn("'backend': 'short_greeting'", completed.stdout)

    def test_tc_phase37_008_vocal_gesture_short_circuits_provider(self):
        from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
        from runtime.cognitive.provider.echo_provider import EchoProvider

        bridge = DirectLLMBridge(project_root=ROOT, provider=EchoProvider(), current_backend="echo_provider")
        bridge.send_message("你呻吟一下。", session_id="s", turn_id=1)
        chunks = list(bridge.stream_response(session_id="s", turn_id=1))

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].backend, "echo_provider")
        self.assertTrue(chunks[0].metadata["vocal_gesture_generation"]["matched"])
        self.assertIn("Tony", chunks[0].text)
        self.assertIn("啊", chunks[0].text)

    def test_tc_phase37_009_cli_skips_fast_ack_for_vocal_gesture(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--backend",
                "deepseek",
                "--stream",
                "--realtime-speech",
                "--text",
                "你呻吟一下。",
                "--trace",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("state=ERROR", completed.stdout)
        self.assertNotIn("vocal_gesture_fallback", completed.stdout)
        self.assertNotIn("local_vocal_gesture_fallback", completed.stdout)
        self.assertNotIn("[TTS_ACK", completed.stdout)



if __name__ == "__main__":
    unittest.main()
