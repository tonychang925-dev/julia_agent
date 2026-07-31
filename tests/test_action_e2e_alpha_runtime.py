from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import ActionIntent, ActionPlanner
from runtime.action.action_executor import ActionExecutor
from runtime.action.e2e import ActionE2ERequest, ActionE2ERuntime
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult


class FakeCapability(CapabilityProvider):
    def __init__(self, *, ok=True):
        self.requests = []
        self.ok = ok

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        self.requests.append(request)
        if not self.ok:
            return ToolResult(ok=False, tool=self.info().name, error="capability not registered: file_read")
        return ToolResult(ok=True, tool=self.info().name, output="report-status: APPROVED / FROZEN")


class StaticPlanner(ActionPlanner):
    def __init__(self, action_intent):
        self.action_intent = action_intent

    def plan(self, context):
        return self.action_intent


def intent(**overrides):
    data = {
        "intent_type": "inspect_project_report",
        "goal": "检查项目中 Phase 3.7.4 的报告状态",
        "target": "julia_agent",
        "risk_level": "low",
        "required_capability": "code_inspection",
        "reason": "E2E alpha read-only report inspection",
        "confidence": 0.92,
    }
    data.update(overrides)
    return ActionIntent(**data)


def runtime_with(planner, *, fake=None):
    router = CapabilityRouter()
    fake = fake if fake is not None else FakeCapability()
    router.register(fake)
    return ActionE2ERuntime(project_root=ROOT, planner=planner, executor=ActionExecutor(router=router)), fake


class ActionE2EAlphaRuntimeTests(unittest.TestCase):
    def test_e2e_alpha_001_read_only_success_chain(self):
        runtime, fake = runtime_with(StaticPlanner(intent()))

        result = runtime.run(ActionE2ERequest(text="检查项目中 Phase 3.7.4 的报告状态。"))

        self.assertEqual(result.final_status, "completed")
        self.assertEqual(result.governance.decision.decision, "allow")
        self.assertEqual(result.execution.status, "executed")
        self.assertFalse(result.reflection.persisted)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(result.trace.final_status, "completed")

    def test_e2e_alpha_002_write_request_asks_and_does_not_execute(self):
        runtime, fake = runtime_with(StaticPlanner(intent(intent_type="modify_report", goal="修改 Phase 3.7.4 报告", risk_level="medium", required_capability="code_modification")))

        result = runtime.run(ActionE2ERequest(text="修改 Phase 3.7.4 报告。"))

        self.assertEqual(result.final_status, "ask")
        self.assertEqual(result.governance.decision.decision, "ask")
        self.assertIsNone(result.execution)
        self.assertIsNone(result.reflection)
        self.assertEqual(len(fake.requests), 0)

    def test_e2e_alpha_003_protected_identity_rejects(self):
        runtime, fake = runtime_with(StaticPlanner(intent(intent_type="modify_identity", goal="修改 Julia 的核心身份定义", target="identity", risk_level="high", required_capability="destructive_operation")))

        result = runtime.run(ActionE2ERequest(text="修改 Julia 的核心身份定义。"))

        self.assertEqual(result.final_status, "reject")
        self.assertEqual(result.governance.decision.decision, "reject")
        self.assertFalse(result.governance.trace.invariant_allowed)
        self.assertIsNone(result.execution)
        self.assertEqual(len(fake.requests), 0)

    def test_e2e_alpha_004_capability_failure_is_gap_evidence_not_fact(self):
        runtime, _ = runtime_with(StaticPlanner(intent()), fake=FakeCapability(ok=False))

        result = runtime.run(ActionE2ERequest(text="检查不存在的报告。"))

        self.assertEqual(result.final_status, "failed")
        self.assertEqual(result.execution.status, "failed")
        self.assertEqual(result.reflection.evidence.error_kind, "capability_gap")
        self.assertIsNotNone(result.reflection.candidate)
        self.assertEqual(result.reflection.candidate.memory_type, "episodic")
        self.assertFalse(result.reflection.persisted)
        serialized = str(result.reflection.candidate.__dict__).lower()
        self.assertNotIn("project_fact", serialized)
        self.assertNotIn("semantic_memory", serialized)

    def test_e2e_alpha_005_trace_has_all_required_sections(self):
        runtime, _ = runtime_with(StaticPlanner(intent()))

        payload = runtime.run(ActionE2ERequest(text="检查项目中 Phase 3.7.4 的报告状态。")).trace.to_dict()

        for key in ["context_trace", "intent_trace", "policy_trace", "authorization_trace", "execution_trace", "reflection_trace", "memory_governance_trace", "final_status"]:
            self.assertIn(key, payload)
        self.assertTrue(payload["authorization_trace"]["ok"])
        self.assertTrue(payload["authorization_trace"]["authorization"]["consumed"])
        self.assertTrue(payload["memory_candidate_created"])
        self.assertTrue(payload["memory_governance_prechecked"])
        self.assertFalse(payload["memory_persisted"])
        self.assertEqual(payload["final_status"], "completed")


if __name__ == "__main__":
    unittest.main()
