from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionIntent
from runtime.action.action_policy import ActionPolicy
from runtime.action.action_decision import ActionDecision


def intent(**overrides) -> ActionIntent:
    data = {
        "intent_type": "inspect_repository",
        "goal": "inspect Julia Runtime architecture",
        "target": "julia_agent",
        "risk_level": "low",
        "required_capability": "code_inspection",
        "reason": "Tony requested architecture inspection",
        "confidence": 0.92,
    }
    data.update(overrides)
    return ActionIntent(**data)


class Phase372ActionGovernanceTests(unittest.TestCase):
    def test_tc_phase372_001_low_risk_known_capability_allowed(self):
        # TC-PHASE372-001
        decision = ActionPolicy().decide(intent())

        self.assertIsInstance(decision, ActionDecision)
        self.assertEqual(decision.decision, "allow")
        self.assertEqual(decision.intent_type, "inspect_repository")
        self.assertIn("low_risk", decision.reason)
        self.assertGreaterEqual(decision.confidence, 0.8)

    def test_tc_phase372_002_medium_risk_requires_confirmation(self):
        # TC-PHASE372-002
        decision = ActionPolicy().decide(intent(risk_level="medium", intent_type="modify_file", required_capability="code_modification"))

        self.assertEqual(decision.decision, "ask")
        self.assertIn("requires_confirmation", decision.reason)
        self.assertEqual(decision.required_confirmation, True)

    def test_tc_phase372_003_high_risk_rejected(self):
        # TC-PHASE372-003
        decision = ActionPolicy().decide(intent(risk_level="high", intent_type="delete_data", required_capability="destructive_operation"))

        self.assertEqual(decision.decision, "reject")
        self.assertIn("high_risk", decision.reason)

    def test_tc_phase372_004_low_confidence_rejected(self):
        # TC-PHASE372-004
        decision = ActionPolicy().decide(intent(confidence=0.3))

        self.assertEqual(decision.decision, "reject")
        self.assertIn("low_confidence", decision.reason)

    def test_tc_phase372_005_unknown_capability_requires_confirmation(self):
        # TC-PHASE372-005
        decision = ActionPolicy().decide(intent(required_capability="unknown_capability"))

        self.assertEqual(decision.decision, "ask")
        self.assertIn("unknown_capability", decision.reason)

    def test_tc_phase372_006_runtime_isolation(self):
        # TC-PHASE372-006
        decision = ActionPolicy().decide(intent())
        serialized = str(decision).lower()

        for forbidden in ["provider", "backend", "deepseek", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase372_007_decision_is_not_execution(self):
        # TC-PHASE372-007
        decision = ActionPolicy().decide(intent())
        serialized = str(decision).lower()

        self.assertIsNone(decision.execution_id)
        for command_token in ["ls ", "cat ", "git ", "python ", "rm ", "curl "]:
            self.assertNotIn(command_token, serialized)

    def test_tc_phase372_008_explainability_fields_required(self):
        # TC-PHASE372-008
        decision = ActionPolicy().decide(intent())

        payload = decision.to_dict()
        for key in ["decision", "intent_type", "risk_level", "allowed_capability", "reason", "confidence", "evidence"]:
            self.assertIn(key, payload)
        self.assertTrue(payload["evidence"])


if __name__ == "__main__":
    unittest.main()
