from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase32CLITests(unittest.TestCase):
    def test_tc_phase32_006_julia_conversation_simulate_prints_acceptance_log(self):
        completed = subprocess.run(
            [sys.executable, "-m", "runtime.conversation_runtime.cli", "--simulate", "--text", "Julia，在吗？"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("Julia Voice Runtime started", output)
        self.assertIn("state=LISTENING", output)
        self.assertIn("state=USER_SPEAKING", output)
        self.assertIn("finalizing...", output)
        self.assertIn("text:\nJulia，在吗？", output)
        self.assertIn("state=LISTENING", output)

    def test_tc_phase32_009_julia_conversation_echo_tts_prints_full_loop(self):
        completed = subprocess.run(
            [sys.executable, "-m", "runtime.conversation_runtime.cli", "--echo-tts", "--text", "Julia，在吗？"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("Julia Voice Runtime started", output)
        self.assertIn("state=LISTENING", output)
        self.assertIn("state=USER_SPEAKING", output)
        self.assertIn("state=FINALIZING", output)
        self.assertIn("text=Julia，在吗？", output)
        self.assertIn("state=THINKING", output)
        self.assertIn("Cognitive response: 你好 Tony，我在。", output)
        self.assertIn("state=SPEAKING", output)
        self.assertIn("[TTS:local_tts] 你好 Tony，我在。", output)
        self.assertIn("state=LISTENING", output)
        self.assertIn("latency=", output)


if __name__ == "__main__":
    unittest.main()
