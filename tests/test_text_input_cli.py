from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TextInputCLITests(unittest.TestCase):
    def run_text_input(self, extra_args: list[str], user_input: str = "今天用文字测试。\n") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--text-input",
                "--text-input-turns",
                "1",
                "--backend",
                "echo",
                "--realtime-speech",
                "--conversation-tts-engine",
                "local",
                "--conversation-tts-mode",
                "dry_run",
                "--trace",
                *extra_args,
            ],
            input=user_input,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=True,
        )

    def test_tc_text_input_001_stdin_turn_bypasses_stt_and_preserves_realtime_tts_trace(self):
        completed = self.run_text_input([])
        output = completed.stdout

        self.assertIn("Julia Voice Runtime started", output)
        self.assertIn("[TEXT_INPUT] stdin text mode enabled", output)
        self.assertIn("[TEXT_TURN] 1/1", output)
        self.assertIn("text=今天用文字测试。", output)
        self.assertIn("state=RESPONDING", output)
        self.assertIn("[TTS_SENTENCE:0:local_tts]", output)
        self.assertIn("trace=", output)
        self.assertIn("'backend': 'echo_adapter'", output)
        self.assertNotIn("[VOICE] 请开始说话", output)
        self.assertNotIn("[STT_EMPTY]", output)
        self.assertEqual("", completed.stderr)

    def test_tc_text_input_002_text_input_takes_precedence_over_real_voice(self):
        completed = self.run_text_input(["--real-voice", "--stt-bin", "/path/that/should/not/run"])
        output = completed.stdout

        self.assertIn("[TEXT_INPUT] stdin text mode enabled", output)
        self.assertIn("text=今天用文字测试。", output)
        self.assertNotIn("[VOICE] 请开始说话", output)
        self.assertNotIn("state=ERROR", output)
        self.assertNotIn("STT", output)
        self.assertEqual("", completed.stderr)

    def test_tc_text_input_003_exit_terms_work_with_bounded_turn_count(self):
        completed = self.run_text_input([], user_input="退出\n")
        output = completed.stdout

        self.assertIn("[TEXT_INPUT] exit requested", output)
        self.assertNotIn("state=THINKING", output)
        self.assertNotIn("state=ERROR", output)
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
