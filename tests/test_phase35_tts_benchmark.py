from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tts.benchmark import TTSBenchmarkRunner
from tts.elevenlabs_tts import ElevenLabsScriptTTSEngine
from tts.local_tts import LocalTTSEngine


class Phase35TTSBenchmarkTests(unittest.TestCase):
    def test_tc_phase35_015_tts_benchmark_measures_dry_run_startup(self):
        report = TTSBenchmarkRunner(LocalTTSEngine(mode="dry_run")).run(text="嗯，Tony，我在想。", repeat=2)

        self.assertEqual(report.count, 2)
        data = report.to_dict()
        self.assertEqual(data["summary"]["ok_count"], 2)
        self.assertEqual(data["summary"]["engine"], "local_tts")
        self.assertIn("call_ms", data["summary"])
        self.assertIn("duration_ms", data["summary"])
        self.assertIn("measured_call_ms", data["samples"][0]["metadata"])

    def test_tc_phase35_016_cli_tts_benchmark_outputs_json_report(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--tts-benchmark",
                "2",
                "--tts-mode",
                "dry_run",
                "--fast-ack",
                "嗯，Tony，我在想。",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        self.assertIn("tts_benchmark=", completed.stdout)
        payload = completed.stdout.split("tts_benchmark=", 1)[1].strip()
        data = json.loads(payload)
        self.assertEqual(data["summary"]["count"], 2)
        self.assertEqual(data["summary"]["engine"], "local_tts")

    def test_tc_phase35_017_elevenlabs_script_benchmark_reports_missing_script_without_network(self):
        missing_script = ROOT / "tmp_missing_el_speak.py"
        report = TTSBenchmarkRunner(ElevenLabsScriptTTSEngine(script_path=missing_script, timeout_s=1)).run(
            text="嗯，Tony，我在想。",
            repeat=1,
        )

        data = report.to_dict()
        self.assertEqual(data["summary"]["engine"], "elevenlabs_script")
        self.assertEqual(data["summary"]["ok_count"], 0)
        self.assertIn("script not found", data["samples"][0]["error"])
        self.assertIn("tts_call_ms", data["samples"][0]["metadata"])

    def test_tc_phase35_018_cli_elevenlabs_script_benchmark_accepts_script_path(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "runtime.conversation_runtime.cli",
                "--tts-benchmark",
                "1",
                "--tts-engine",
                "elevenlabs-script",
                "--elevenlabs-script",
                str(ROOT / "tmp_missing_el_speak.py"),
                "--tts-timeout",
                "1",
                "--fast-ack",
                "嗯，Tony，我在想。",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        payload = completed.stdout.split("tts_benchmark=", 1)[1].strip()
        data = json.loads(payload)
        self.assertEqual(data["summary"]["engine"], "elevenlabs_script")
        self.assertEqual(data["summary"]["ok_count"], 0)

    def test_tc_phase35_019_elevenlabs_script_requires_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "fake_el_speak.py"
            script.write_text("#!/usr/bin/env python3\nprint('should not run')\n", encoding="utf-8")
            script.chmod(0o755)
            old_key = os.environ.pop("ELEVENLABS_API_KEY", None)
            try:
                result = ElevenLabsScriptTTSEngine(
                    script_path=script,
                    timeout_s=1,
                    require_enabled_flag=False,
                ).speak("测试")
            finally:
                if old_key is not None:
                    os.environ["ELEVENLABS_API_KEY"] = old_key

            self.assertFalse(result.ok)
            self.assertIn("ELEVENLABS_API_KEY", result.error or "")

    def test_tc_phase35_020_elevenlabs_script_reports_script_api_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "fake_el_speak.py"
            script.write_text("#!/usr/bin/env python3\nprint('API Error: bad key')\n", encoding="utf-8")
            script.chmod(0o755)
            old_key = os.environ.get("ELEVENLABS_API_KEY")
            os.environ["ELEVENLABS_API_KEY"] = "test-key"
            try:
                result = ElevenLabsScriptTTSEngine(
                    script_path=script,
                    timeout_s=1,
                    require_enabled_flag=False,
                ).speak("测试")
            finally:
                if old_key is None:
                    os.environ.pop("ELEVENLABS_API_KEY", None)
                else:
                    os.environ["ELEVENLABS_API_KEY"] = old_key

            self.assertFalse(result.ok)
            self.assertIn("API Error", result.error or "")


if __name__ == "__main__":
    unittest.main()
