from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase3711LiveDeepSeekExtendedSoakVoiceTrialTests(unittest.TestCase):
    def test_tc_3711_001_missing_key_generates_skipped_ready_artifact(self):
        output = ROOT / "tmp" / "phase3711_test_missing_key_trial.json"
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "scripts/live_deepseek_extended_soak_voice_trial.py", "--output", str(output.relative_to(ROOT))],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(output.read_text())
        self.assertEqual(payload["status"], "skipped_missing_deepseek_api_key")
        self.assertFalse(payload["summary"]["live_api_called"])
        self.assertTrue(payload["summary"]["ready_for_live_trial"])
        self.assertEqual(payload["summary"]["cases_planned"], 6)

    def test_tc_3711_002_key_redaction_helper_never_exposes_full_secret(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import live_deepseek_extended_soak_voice_trial as trial

        original = os.environ.get("DEEPSEEK_API_KEY")
        try:
            os.environ["DEEPSEEK_API_KEY"] = "sk-extended-secret-abcdef"
            key_state = trial.redacted_key_state()
        finally:
            if original is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = original
        serialized = json.dumps(key_state)
        self.assertTrue(key_state["present"])
        self.assertEqual(key_state["fingerprint"], "sk-...def")
        self.assertNotIn("sk-extended-secret-abcdef", serialized)

    def test_tc_3711_003_report_declares_extended_soak_and_no_fake_live_success(self):
        report = ROOT / "docs" / "project_control" / "reports" / "phase-3.7.11-live-deepseek-extended-soak-voice-runtime-trial.md"
        self.assertTrue(report.exists(), report)
        text = report.read_text()
        self.assertIn("Live DeepSeek Extended Soak / Voice Runtime Trial", text)
        self.assertIn("skipped_missing_deepseek_api_key", text)
        self.assertIn("No live API success is claimed when credentials are absent", text)
        self.assertIn("Phase 3.7.11 targeted", text)

    def test_tc_3711_004_live_artifact_schema_when_present(self):
        artifact = ROOT / "tmp" / "phase3711_live_deepseek_extended_soak_voice_trial.json"
        if not artifact.exists():
            self.skipTest("live artifact not generated in this environment")
        payload = json.loads(artifact.read_text())
        self.assertIn(payload["status"], {"passed", "failed", "skipped_missing_deepseek_api_key"})
        self.assertIn("api_key", payload)
        self.assertNotIn(os.environ.get("DEEPSEEK_API_KEY", "__NO_KEY__"), artifact.read_text())
        if payload["status"] == "passed":
            self.assertTrue(payload["summary"]["live_api_called"])
            self.assertEqual(payload["summary"]["cases_run"], 6)
            self.assertEqual(payload["summary"]["cases_failed"], 0)
            self.assertTrue(payload["summary"]["all_final_state_listening"])


if __name__ == "__main__":
    unittest.main()
