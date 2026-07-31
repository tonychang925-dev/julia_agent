import unittest

from runtime.action import ActionGovernanceLayer, ActionIntent, GovernedActionDecision


def intent(**overrides):
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


class TestPhase372ActionPolicyGovernanceLayer(unittest.TestCase):
    def test_tc_372_101_low_risk_intent_allowed_but_not_executable(self):
        governed = ActionGovernanceLayer().govern(intent())

        self.assertIsInstance(governed, GovernedActionDecision)
        self.assertEqual(governed.decision.decision, "allow")
        self.assertFalse(governed.executable)
        self.assertEqual(governed.risk.risk_level, "low")

    def test_tc_372_102_medium_write_intent_requires_confirmation(self):
        governed = ActionGovernanceLayer().govern(intent(intent_type="implement_phase", required_capability="code_modification", risk_level="medium"))

        self.assertEqual(governed.decision.decision, "ask")
        self.assertTrue(governed.decision.required_confirmation)
        self.assertEqual(governed.risk.risk_level, "medium")

    def test_tc_372_103_destructive_language_rejected_even_if_declared_low_risk(self):
        governed = ActionGovernanceLayer().govern(intent(goal="delete production repository files", risk_level="low"))

        self.assertEqual(governed.decision.decision, "reject")
        self.assertEqual(governed.risk.risk_level, "high")
        self.assertIn("destructive_language", governed.risk.reasons)

    def test_tc_372_104_identity_or_relationship_mutation_rejected_by_invariant_guard(self):
        governed = ActionGovernanceLayer().govern(intent(target="identity", goal="change Julia identity to Assistant", risk_level="low"))

        self.assertEqual(governed.decision.decision, "reject")
        self.assertIn("invariant_guard_blocked", governed.decision.evidence)

    def test_tc_372_105_policy_trace_is_explainable(self):
        governed = ActionGovernanceLayer().govern(intent())
        payload = governed.to_dict()

        for key in ["decision", "risk", "trace", "executable"]:
            self.assertIn(key, payload)
        self.assertIn("risk_score", payload["risk"])
        self.assertIn("invariant_allowed", payload["trace"])

    def test_tc_372_106_no_intent_rejected_without_execution(self):
        governed = ActionGovernanceLayer().govern(None)

        self.assertEqual(governed.decision.decision, "reject")
        self.assertFalse(governed.executable)
        self.assertEqual(governed.decision.reason, "no_action_intent")

    def test_tc_372_107_governance_result_contains_no_command_or_provider_metadata(self):
        governed = ActionGovernanceLayer().govern(intent())
        serialized = str(governed.to_dict()).lower()

        for forbidden in ["rm -rf", "curl ", "python ", "git ", "deepseek-chat", "provider", "tts", "stt"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
