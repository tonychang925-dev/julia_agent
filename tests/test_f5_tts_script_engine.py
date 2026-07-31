import unittest

from tts.f5_tts import F5TTSScriptEngine


class F5TTSScriptEngineTests(unittest.TestCase):
    def test_f5_tts_engine_reports_disabled_when_flag_missing(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as td:
            tmp_path = Path(td)
            worker = tmp_path / "f5_worker.py"
            worker.write_text("print('should not run')")
            engine = F5TTSScriptEngine(worker_path=worker, enabled_flag_path=tmp_path / "missing", python_bin="python3")

            result = engine.speak("Tony，我在。")

            self.assertFalse(result.ok)
            self.assertEqual(result.engine, "f5_tts_warm_worker")
            self.assertIn("TTS disabled", result.error or "")

    def test_f5_tts_engine_invokes_warm_worker_when_enabled(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as td:
            tmp_path = Path(td)
            worker = tmp_path / "f5_worker.py"
            worker.write_text(
                "import json, sys\n"
                "print(json.dumps({'ready': True}), flush=True)\n"
                "for line in sys.stdin:\n"
                "    if line.strip() == '__quit__': print(json.dumps({'ok': True, 'quit': True}), flush=True); break\n"
                "    print(json.dumps({'ok': True, 'audio_path': '/tmp/fake.wav'}), flush=True)\n"
            )
            flag = tmp_path / "tts_enabled"
            flag.write_text("1")
            engine = F5TTSScriptEngine(worker_path=worker, enabled_flag_path=flag, python_bin="python3", timeout_s=5, playback="none")

            try:
                result = engine.speak("Tony，我在。")
            finally:
                engine._stop_worker()

            self.assertTrue(result.ok)
            self.assertEqual(result.engine, "f5_tts_warm_worker")
            self.assertEqual(result.metadata["audio_path"], "/tmp/fake.wav")


if __name__ == "__main__":
    unittest.main()
