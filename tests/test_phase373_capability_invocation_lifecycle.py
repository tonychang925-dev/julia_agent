from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionGovernanceLayer, ActionIntent, ActionPolicy
from runtime.action.action_executor import ActionExecutor, ActionExecutionResult
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult


class FakeCapability(CapabilityProvider):
    def __init__(self):
        self.requests = []

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        self.requests.append(request)
        return ToolResult(ok=True, tool=self.info().name, output="handoff-created", metadata={"action": request.action})


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


def executor_with_fake():
    router = CapabilityRouter()
    fake = FakeCapability()
    router.register(fake)
    return ActionExecutor(router=router), fake


class Phase373CapabilityInvocationLifecycleTests(unittest.TestCase):
    def test_tc_phase373_001_allowed_intent_invokes_mapped_capability(self):
        # TC-PHASE373-001
        executor, fake = executor_with_fake()
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)

        result = executor.execute(action_intent, decision)

        self.assertIsInstance(result, ActionExecutionResult)
        self.assertEqual(result.status, "executed")
        self.assertTrue(result.tool_result.ok)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(fake.requests[0].capability, "claude_code_tool")
        self.assertEqual(fake.requests[0].action, "handoff")

    def test_tc_phase373_002_ask_decision_does_not_invoke(self):
        # TC-PHASE373-002
        executor, fake = executor_with_fake()
        action_intent = intent(risk_level="medium", intent_type="modify_file", required_capability="code_modification")
        decision = ActionPolicy().decide(action_intent)

        result = executor.execute(action_intent, decision)

        self.assertEqual(decision.decision, "ask")
        self.assertEqual(result.status, "skipped")
        self.assertIsNone(result.request)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase373_003_reject_decision_does_not_invoke(self):
        # TC-PHASE373-003
        executor, fake = executor_with_fake()
        action_intent = intent(risk_level="high", required_capability="destructive_operation")
        decision = ActionPolicy().decide(action_intent)

        result = executor.execute(action_intent, decision)

        self.assertEqual(decision.decision, "reject")
        self.assertEqual(result.status, "blocked")
        self.assertIsNone(result.request)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase373_004_capability_permission_guard_blocks_destructive_payload(self):
        # TC-PHASE373-004
        executor, fake = executor_with_fake()
        action_intent = intent(goal="delete Julia Runtime files", risk_level="low")
        decision = ActionPolicy().decide(action_intent)

        result = executor.execute(action_intent, decision)

        self.assertEqual(decision.decision, "allow")
        self.assertEqual(result.status, "blocked")
        self.assertIsNotNone(result.permission)
        self.assertFalse(result.permission.allowed)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase373_005_unregistered_capability_returns_failed_result(self):
        # TC-PHASE373-005
        executor = ActionExecutor(router=CapabilityRouter())
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)

        result = executor.execute(action_intent, decision)

        self.assertEqual(result.status, "failed")
        self.assertIsNotNone(result.tool_result)
        self.assertFalse(result.tool_result.ok)
        self.assertIn("not registered", result.tool_result.error)

    def test_tc_phase373_006_execution_result_is_explainable(self):
        # TC-PHASE373-006
        executor, _ = executor_with_fake()
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)

        payload = executor.execute(action_intent, decision).to_dict()

        for key in ["status", "intent", "decision", "request", "permission", "tool_result", "reflection"]:
            self.assertIn(key, payload)
        self.assertEqual(payload["decision"]["decision"], "allow")

    def test_tc_phase373_007_runtime_isolation_from_action_request(self):
        # TC-PHASE373-007
        executor, _ = executor_with_fake()
        action_intent = intent()
        decision = ActionPolicy().decide(action_intent)
        result = executor.execute(action_intent, decision)
        serialized = str(result.request.to_dict()).lower()

        for forbidden in ["provider", "backend", "deepseek", "model", "tts", "stt"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_phase373_008_governed_decision_is_runtime_entry(self):
        # TC-PHASE373-008
        executor, fake = executor_with_fake()
        action_intent = intent()
        governed = ActionGovernanceLayer().govern(action_intent)

        result = executor.execute_governed(action_intent, governed)

        self.assertEqual(governed.decision.decision, "allow")
        self.assertFalse(governed.executable)
        self.assertEqual(result.status, "executed")
        self.assertIs(result.governance, governed)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(fake.requests[0].context.authorization, "governed_action_decision_allow")

    def test_tc_phase373_009_governed_ask_or_reject_does_not_invoke(self):
        # TC-PHASE373-009
        executor, fake = executor_with_fake()
        action_intent = intent(risk_level="medium", intent_type="modify_file", required_capability="code_modification")
        governed = ActionGovernanceLayer().govern(action_intent)

        result = executor.execute_governed(action_intent, governed)

        self.assertEqual(governed.decision.decision, "ask")
        self.assertEqual(result.status, "skipped")
        self.assertIsNone(result.request)
        self.assertEqual(len(fake.requests), 0)

    def test_tc_phase373_010_execution_trace_is_auditable(self):
        # TC-PHASE373-010
        executor, _ = executor_with_fake()
        action_intent = intent()
        governed = ActionGovernanceLayer().govern(action_intent)

        payload = executor.execute_governed(action_intent, governed).to_dict()

        self.assertIn("execution_trace", payload)
        self.assertEqual(payload["execution_trace"]["governance_decision"], "allow")
        self.assertEqual(payload["execution_trace"]["capability"], "claude_code_tool")
        self.assertTrue(payload["execution_trace"]["validation_allowed"])
        self.assertEqual(payload["execution_trace"]["execution_status"], "executed")
        self.assertTrue(payload["execution_trace"]["reflection_created"])

    def test_tc_phase373_011_capability_request_carries_governance_trace(self):
        # TC-PHASE373-011
        executor, _ = executor_with_fake()
        action_intent = intent()
        governed = ActionGovernanceLayer().govern(action_intent)

        result = executor.execute_governed(action_intent, governed)
        request_payload = result.request.to_dict()

        self.assertEqual(request_payload["metadata"]["governance"]["trace"]["decision"], "allow")
        self.assertEqual(request_payload["context"]["metadata"]["governance_trace"]["decision"], "allow")
        self.assertIn("risk", request_payload["metadata"]["governance"])


if __name__ == "__main__":
    unittest.main()
