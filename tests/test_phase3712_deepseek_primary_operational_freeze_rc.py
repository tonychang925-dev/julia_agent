from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase3712DeepSeekPrimaryOperationalFreezeRCTests(unittest.TestCase):
    def test_tc_3712_001_manifest_declares_release_candidate_state(self):
        path = ROOT / "tmp" / "phase3712_deepseek_primary_operational_freeze_manifest.json"
        self.assertTrue(path.exists(), path)
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["status"], "release_candidate")
        self.assertEqual(manifest["primary_provider"], "deepseek")
        self.assertEqual(manifest["fallback_provider"], "codex")
        self.assertTrue(manifest["provider_alignment"]["frozen"])
        self.assertEqual(manifest["release_candidate"]["default_runtime_provider"], "deepseek")
        self.assertIn("DEEPSEEK_API_KEY", manifest["release_candidate"]["requires_env"])

    def test_tc_3712_002_all_evidence_phases_are_accepted_frozen_and_linked(self):
        manifest = json.loads((ROOT / "tmp" / "phase3712_deepseek_primary_operational_freeze_manifest.json").read_text())
        for phase in ("3.7.9.1", "3.7.9.2", "3.7.9.3", "3.7.9.4", "3.7.9.5", "3.7.10", "3.7.11"):
            with self.subTest(phase=phase):
                evidence = manifest["evidence"][phase]
                self.assertEqual(evidence["decision"], "ACCEPT")
                self.assertEqual(evidence["status"], "APPROVED-FROZEN")
                self.assertTrue((ROOT / evidence["report"]).exists())
                gate = ROOT / "tmp" / "runs" / f"phase-{phase}" / "gate_decision.json"
                self.assertTrue(gate.exists(), gate)
                payload = json.loads(gate.read_text())
                self.assertEqual(payload["decision"], "ACCEPT")
                self.assertEqual(payload["status"], "APPROVED-FROZEN")

    def test_tc_3712_003_live_artifacts_confirm_success_without_secret_leakage(self):
        for rel, expected_cases in (
            ("tmp/phase3710_live_deepseek_primary_runtime_trial.json", 3),
            ("tmp/phase3711_live_deepseek_extended_soak_voice_trial.json", 6),
        ):
            with self.subTest(artifact=rel):
                artifact = ROOT / rel
                self.assertTrue(artifact.exists(), artifact)
                text = artifact.read_text()
                payload = json.loads(text)
                self.assertEqual(payload["status"], "passed")
                self.assertTrue(payload["summary"]["live_api_called"])
                self.assertEqual(payload["summary"]["cases_run"], expected_cases)
                self.assertEqual(payload["summary"]["cases_failed"], 0)
                fingerprint = payload["api_key"].get("fingerprint")
                self.assertTrue(fingerprint is None or "..." in fingerprint)

    def test_tc_3712_004_runtime_invariants_are_all_validated(self):
        manifest = json.loads((ROOT / "tmp" / "phase3712_deepseek_primary_operational_freeze_manifest.json").read_text())
        for invariant, status in manifest["runtime_invariants"].items():
            with self.subTest(invariant=invariant):
                self.assertEqual(status, "validated")

    def test_tc_3712_005_report_contains_operational_commands_and_rollback(self):
        report = ROOT / "docs" / "project_control" / "reports" / "phase-3.7.12-deepseek-primary-operational-freeze-release-candidate.md"
        self.assertTrue(report.exists(), report)
        text = report.read_text()
        for expected in (
            "DeepSeek Primary Operational Freeze",
            "primary_provider = deepseek",
            "provider_output_authority = metadata-only",
            "python3 -m runtime.conversation_runtime.cli --echo-tts --backend deepseek --enable-action-loop --realtime-speech",
            "backend deepseek → backend codex or direct-echo",
            "ACCEPT WITH NOTES / APPROVED-FROZEN",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
