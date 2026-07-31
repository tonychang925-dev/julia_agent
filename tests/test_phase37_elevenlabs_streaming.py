from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase37ElevenLabsStreamingTests(unittest.TestCase):
    def test_tc_phase37_006_streaming_engine_requires_api_key(self):
        from tts.elevenlabs_streaming_tts import ElevenLabsStreamingTTSEngine

        old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            result = ElevenLabsStreamingTTSEngine(require_enabled_flag=False).speak("测试")
        finally:
            if old_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = old_key

        self.assertFalse(result.ok)
        self.assertIn("ELEVENLABS_API_KEY", result.error or "")
        self.assertEqual(result.engine, "elevenlabs_streaming")

    def test_tc_phase37_007_cli_accepts_elevenlabs_streaming_benchmark_engine(self):
        old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--tts-benchmark",
                    "1",
                    "--tts-engine",
                    "elevenlabs-stream",
                    "--tts-timeout",
                    "1",
                    "--text",
                    "测试",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        finally:
            if old_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = old_key

        self.assertIn('"engine": "elevenlabs_streaming"', completed.stdout)
        self.assertIn("ELEVENLABS_API_KEY", completed.stdout)


    def test_tc_phase37_010_cli_accepts_elevenlabs_model_override(self):
        old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--tts-benchmark",
                    "1",
                    "--tts-engine",
                    "elevenlabs-stream",
                    "--elevenlabs-model",
                    "eleven_v3",
                    "--tts-timeout",
                    "1",
                    "--text",
                    "测试",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        finally:
            if old_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = old_key

        self.assertIn('"engine": "elevenlabs_streaming"', completed.stdout)
        self.assertIn("ELEVENLABS_API_KEY", completed.stdout)


if __name__ == "__main__":
    unittest.main()
