from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase3710LiveDeepSeekPrimaryRuntimeTrialTests(unittest.TestCase):
    def test_tc_3710_001_missing_key_generates_skipped_ready_artifact_without_live_claim(self):
        output = ROOT / "tmp" / "phase3710_test_missing_key_trial.json"
        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "scripts/live_deepseek_primary_runtime_trial.py", "--output", str(output.relative_to(ROOT))],
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
        self.assertEqual(payload["summary"]["cases_planned"], 3)

    def test_tc_3710_002_artifact_schema_redacts_credentials(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import live_deepseek_primary_runtime_trial as trial

        original = os.environ.get("DEEPSEEK_API_KEY")
        try:
            os.environ["DEEPSEEK_API_KEY"] = "sk-test-secret-123456"
            key_state = trial._redacted_key_state()
        finally:
            if original is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = original

        serialized = json.dumps(key_state)
        self.assertTrue(key_state["present"])
        self.assertEqual(key_state["fingerprint"], "sk-...456")
        self.assertNotIn("sk-test-secret-123456", serialized)

    def test_tc_3710_003_report_declares_live_status_without_fabricating_api_success(self):
        report = ROOT / "docs" / "project_control" / "reports" / "phase-3.7.10-live-deepseek-primary-runtime-trial.md"
        self.assertTrue(report.exists(), report)
        text = report.read_text()
        self.assertIn("DEEPSEEK_API_KEY", text)
        self.assertIn("skipped_missing_deepseek_api_key", text)
        self.assertIn("No live API success is claimed when credentials are absent", text)
        self.assertIn("Phase 3.7.10 targeted", text)


if __name__ == "__main__":
    unittest.main()
