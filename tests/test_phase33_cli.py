from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase33CLITests(unittest.TestCase):
    def test_tc_phase33_007_cli_direct_echo_backend_runs_without_claude_host(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--stream",
                "--realtime-speech",
                "--backend",
                "direct-echo",
                "--text",
                "Julia，你是谁？",
                "--trace",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("state=THINKING", output)
        self.assertIn("我是Julia", output)
        self.assertIn("Tony", output)
        self.assertIn("'backend': 'echo_provider'", output)
        self.assertIn("'bridge': 'direct_llm'", output)
        self.assertIn("[TTS_SENTENCE:0:local_tts]", output)

    def test_tc_phase33_020_cli_deepseek_realtime_defaults_fast_ack_even_when_provider_errors(self):
        import os
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--stream",
                "--realtime-speech",
                "--backend",
                "deepseek",
                "--text",
                "Julia，你是谁？",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("[TTS_ACK:local_tts] 嗯，Tony，我在想。", completed.stdout)
        self.assertIn("state=ERROR", completed.stdout)

    def test_tc_phase33_021_cli_deepseek_realtime_can_disable_default_fast_ack(self):
        import os
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--stream",
                "--realtime-speech",
                "--backend",
                "deepseek",
                "--no-fast-ack",
                "--text",
                "Julia，你是谁？",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertNotIn("[TTS_ACK", completed.stdout)
        self.assertIn("state=ERROR", completed.stdout)

    def test_tc_phase33_022_cli_deepseek_realtime_can_override_default_fast_ack(self):
        import os
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--stream",
                "--realtime-speech",
                "--backend",
                "deepseek",
                "--fast-ack",
                "嗯，Tony，我马上看。",
                "--text",
                "Julia，你是谁？",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("[TTS_ACK:local_tts] 嗯，Tony，我马上看。", completed.stdout)
        self.assertNotIn("[TTS_ACK:local_tts] 嗯，Tony，我在想。", completed.stdout)

    def test_tc_phase33_023_cli_deepseek_real_voice_disables_default_fast_ack(self):
        from types import SimpleNamespace
        from runtime.conversation_runtime.cli import default_fast_ack_for_args

        args = SimpleNamespace(
            backend="deepseek",
            realtime_speech=True,
            no_fast_ack=False,
            real_voice=True,
        )

        self.assertEqual(default_fast_ack_for_args(args), "")

    def test_tc_phase33_024_cli_deepseek_text_realtime_keeps_default_fast_ack(self):
        from types import SimpleNamespace
        from runtime.conversation_runtime.cli import default_fast_ack_for_args

        args = SimpleNamespace(
            backend="deepseek",
            realtime_speech=True,
            no_fast_ack=False,
            real_voice=False,
        )

        self.assertEqual(default_fast_ack_for_args(args), "嗯，Tony，我在想。")


    def test_tc_phase3510_025_cli_real_voice_deepseek_does_not_default_fixed_relationship_mode(self):
        from types import SimpleNamespace
        from runtime.conversation_runtime.cli import relationship_mode_for_args

        args = SimpleNamespace(
            backend="deepseek",
            real_voice=True,
            realtime_speech=True,
            relationship_mode=None,
        )

        self.assertIsNone(relationship_mode_for_args(args))

    def test_tc_phase33_026_cli_relationship_mode_override_wins(self):
        from types import SimpleNamespace
        from runtime.conversation_runtime.cli import relationship_mode_for_args

        args = SimpleNamespace(
            backend="deepseek",
            real_voice=True,
            realtime_speech=True,
            relationship_mode="engineering_collaboration",
        )

        self.assertEqual(relationship_mode_for_args(args), "engineering_collaboration")



if __name__ == "__main__":
    unittest.main()

class Phase33DeepSeekCLITests(unittest.TestCase):
    def test_tc_phase33_012_cli_deepseek_backend_reports_structured_error_without_key_override(self):
        import os
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--echo-tts",
                "--stream",
                "--realtime-speech",
                "--backend",
                "deepseek",
                "--text",
                "Julia，你是谁？",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("state=THINKING", output)
        self.assertIn("state=ERROR", output)
