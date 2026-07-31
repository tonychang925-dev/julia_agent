from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionGovernanceLayer, ActionIntent, ActionPolicy, ActionReflectionEngine
from runtime.action.action_executor import ActionExecutor
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult
from runtime.memory import MemoryObject
from runtime.reflection.memory_candidate import MemoryCandidate


class FakeCapability(CapabilityProvider):
    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        return ToolResult(ok=True, tool=self.info().name, output="inspection-complete")


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


def executor_with_fake() -> ActionExecutor:
    router = CapabilityRouter()
    router.register(FakeCapability())
    return ActionExecutor(router=router)


class Phase374ActionReflectionMemoryIntegrationTests(unittest.TestCase):
    def test_tc_phase374_001_executed_action_creates_memory_candidate(self):
        # TC-PHASE374-001
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)
        result = executor_with_fake().execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)

        self.assertIsInstance(candidate, MemoryCandidate)
        self.assertEqual(candidate.source, "action_reflection")
        self.assertEqual(candidate.memory_type, "episodic")
        self.assertIn("governed action", candidate.summary)
        self.assertIn("Julia Runtime", candidate.topics)
        self.assertIn("Capability Lifecycle", candidate.topics)

    def test_tc_phase374_002_skipped_ask_decision_does_not_create_long_term_candidate(self):
        # TC-PHASE374-002
        action_intent = intent(risk_level="medium", intent_type="modify_file", required_capability="code_modification")
        decision = ActionPolicy().decide(action_intent)
        result = executor_with_fake().execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)

        self.assertEqual(result.status, "skipped")
        self.assertIsNone(candidate)

    def test_tc_phase374_003_unregistered_capability_creates_capability_gap_candidate(self):
        # TC-PHASE374-003
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)
        result = ActionExecutor(router=CapabilityRouter()).execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)

        self.assertEqual(result.status, "failed")
        self.assertIsInstance(candidate, MemoryCandidate)
        self.assertIn("capability_gap", candidate.reason)
        self.assertGreaterEqual(candidate.importance["technical"], 0.7)
        self.assertIn("Capability Gap", candidate.topics)

    def test_tc_phase374_004_permission_block_creates_governance_candidate(self):
        # TC-PHASE374-004
        action_intent = intent(goal="delete Julia Runtime files", risk_level="low")
        decision = ActionPolicy().decide(action_intent)
        result = executor_with_fake().execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)

        self.assertEqual(result.status, "blocked")
        self.assertIsInstance(candidate, MemoryCandidate)
        self.assertIn("permission_guard_blocked", candidate.reason)
        self.assertIn("Action Governance", candidate.topics)

    def test_tc_phase374_005_candidate_has_runtime_isolation_from_provider_metadata(self):
        # TC-PHASE374-005
        action_intent = intent(reason="provider deepseek backend model tts stt latency session_id turn_id noise")
        decision = ActionPolicy().decide(action_intent)
        result = executor_with_fake().execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)
        serialized = str(candidate.__dict__).lower()

        for forbidden in ["provider", "backend", "deepseek", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase374_006_reflection_outputs_candidate_not_persisted_memory_object(self):
        # TC-PHASE374-006
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)
        result = executor_with_fake().execute(action_intent, decision)

        candidate = ActionReflectionEngine().reflect(result)

        self.assertIsInstance(candidate, MemoryCandidate)
        self.assertNotIsInstance(candidate, MemoryObject)
        self.assertFalse(hasattr(candidate, "id"))

    def test_tc_phase374_007_evidence_extraction_is_sanitized(self):
        # TC-PHASE374-007
        action_intent = intent(reason="provider deepseek backend model tts stt latency session_id turn_id noise")
        governed = ActionGovernanceLayer().govern(action_intent)
        result = executor_with_fake().execute_governed(action_intent, governed)

        evidence = ActionReflectionEngine().extract_evidence(result)
        serialized = str(evidence.to_dict()).lower()

        self.assertEqual(evidence.status, "executed")
        self.assertEqual(evidence.intent_type, "inspect_repository")
        self.assertEqual(evidence.capability, "code_inspection")
        self.assertTrue(evidence.tool_ok)
        for forbidden in ["provider", "backend", "deepseek", "model", "latency", "tts", "stt", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase374_008_reflection_review_runs_memory_governance_without_persistence(self):
        # TC-PHASE374-008
        action_intent = intent()
        governed = ActionGovernanceLayer().govern(action_intent)
        result = executor_with_fake().execute_governed(action_intent, governed)

        review = ActionReflectionEngine().reflect_with_governance(result)

        self.assertIsInstance(review.candidate, MemoryCandidate)
        self.assertIsNotNone(review.governance_decision)
        self.assertFalse(review.persisted)
        self.assertNotIn(review.governance_decision.memory_class, ["core_identity", "relationship_foundation"])
        self.assertIn(review.governance_decision.memory_class, ["project_milestone", "normal_episode"])

    def test_tc_phase374_009_skipped_result_has_evidence_but_no_candidate_or_governance(self):
        # TC-PHASE374-009
        action_intent = intent(risk_level="medium", intent_type="modify_file", required_capability="code_modification")
        governed = ActionGovernanceLayer().govern(action_intent)
        result = executor_with_fake().execute_governed(action_intent, governed)

        review = ActionReflectionEngine().reflect_with_governance(result)

        self.assertEqual(review.evidence.status, "skipped")
        self.assertIsNone(review.candidate)
        self.assertIsNone(review.governance_decision)
        self.assertFalse(review.persisted)

    def test_tc_phase374_010_failure_evidence_captures_capability_gap(self):
        # TC-PHASE374-010
        action_intent = intent()
        governed = ActionGovernanceLayer().govern(action_intent)
        result = ActionExecutor(router=CapabilityRouter()).execute_governed(action_intent, governed)

        review = ActionReflectionEngine().reflect_with_governance(result)

        self.assertEqual(result.status, "failed")
        self.assertEqual(review.evidence.error_kind, "capability_gap")
        self.assertIsInstance(review.candidate, MemoryCandidate)
        self.assertIn("capability_gap", review.candidate.reason)
        self.assertIsNotNone(review.governance_decision)


if __name__ == "__main__":
    unittest.main()
