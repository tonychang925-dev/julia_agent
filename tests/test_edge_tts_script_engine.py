import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tts.edge_tts import EdgeScriptTTSEngine


class EdgeScriptTTSEngineTests(unittest.TestCase):
    def test_edge_tts_engine_reports_disabled_when_flag_missing(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            script = tmp / "el_speak_edge.py"
            script.write_text("print('should not run')")
            engine = EdgeScriptTTSEngine(script_path=script, enabled_flag_path=tmp / "missing", python_bin="python3")
            result = engine.speak("Tony，我在。")
            self.assertFalse(result.ok)
            self.assertEqual(result.engine, "edge_tts_script")
            self.assertIn("TTS disabled", result.error or "")

    def test_edge_tts_engine_invokes_script_when_enabled(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            script = tmp / "el_speak_edge.py"
            script.write_text("print('edge ok')")
            flag = tmp / "tts_enabled"
            flag.write_text("1")
            engine = EdgeScriptTTSEngine(script_path=script, enabled_flag_path=flag, python_bin="python3", timeout_s=5)
            result = engine.speak("Tony，我在。")
            self.assertTrue(result.ok)
            self.assertEqual(result.engine, "edge_tts_script")
            self.assertIn("edge ok", result.metadata["script_output"])


if __name__ == "__main__":
    unittest.main()
