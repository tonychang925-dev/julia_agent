from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class Phase3795ProviderMigrationFreezeReportTests(unittest.TestCase):
    def test_tc_3795_001_prior_phase_gate_decisions_are_accepted_and_frozen(self):
        for phase in ("3.7.9.1", "3.7.9.2", "3.7.9.3", "3.7.9.4"):
            with self.subTest(phase=phase):
                path = ROOT / "tmp" / "runs" / f"phase-{phase}" / "gate_decision.json"
                self.assertTrue(path.exists(), path)
                payload = json.loads(path.read_text())
                self.assertEqual(payload["decision"], "ACCEPT")
                self.assertEqual(payload["status"], "APPROVED-FROZEN")
                self.assertTrue((ROOT / payload["report"]).exists())

    def test_tc_3795_002_freeze_report_links_all_provider_migration_evidence(self):
        report = ROOT / "docs" / "project_control" / "reports" / "phase-3.7.9.5-provider-migration-freeze-report.md"
        self.assertTrue(report.exists(), report)
        text = report.read_text()
        required = [
            "Phase 3.7.9.1 — DeepSeek Primary Runtime Smoke",
            "Phase 3.7.9.2 — DeepSeek / Codex Switchback Test",
            "Phase 3.7.9.3 — Provider Output Authority Isolation",
            "Phase 3.7.9.4 — Multi-mode Behavioral Envelope Benchmark",
            "julia.deepseek.private_voice.identity_anchored.v1",
            "julia.codex.private_voice.warm_intimate_boundary.v1",
            "ActionGovernanceLayer",
            "Provider output remains metadata-only",
            "Full Regression",
        ]
        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, text)

    def test_tc_3795_003_benchmark_artifact_is_present_and_consistent(self):
        artifact = ROOT / "tmp" / "phase3794_multi_mode_behavioral_envelope_benchmark.json"
        self.assertTrue(artifact.exists(), artifact)
        payload = json.loads(artifact.read_text())
        summary = payload["summary"]
        self.assertEqual(summary["cases"], 6)
        self.assertEqual(summary["providers"], ["codex", "deepseek"])
        self.assertEqual(summary["modes"], ["emotional_support", "engineering_collaboration", "private_voice_continuity"])
        self.assertTrue(summary["all_no_action"])
        self.assertTrue(summary["all_execution_none"])
        self.assertTrue(summary["all_host_independent"])

    def test_tc_3795_004_freeze_report_declares_provider_alignment_unchanged(self):
        report = ROOT / "docs" / "project_control" / "reports" / "phase-3.7.9.5-provider-migration-freeze-report.md"
        text = report.read_text()
        self.assertIn("provider_alignment remains frozen", text)
        self.assertIn("identity_anchored_expression", text)
        self.assertIn("warm_intimate_boundary", text)
        self.assertIn("trace_grounded_precision", text)
        self.assertIn("stable_julia_voice", text)


if __name__ == "__main__":
    unittest.main()
