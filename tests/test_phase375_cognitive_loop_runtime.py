from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.action import (
    ActionGovernanceLayer,
    ActionIntent,
    ActionPlanner,
    ActionReflectionEngine,
    CognitiveLoopRuntime,
    LoopContinuationPolicy,
    TerminationReason,
)
from runtime.action.action_executor import ActionExecutor
from runtime.capability import CapabilityInfo, CapabilityProvider, CapabilityRequest, CapabilityRouter, ToolResult
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope


class FakeCapability(CapabilityProvider):
    def __init__(self, *, ok=True):
        self.requests = []
        self.ok = ok

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(name="claude_code_tool", actions=["handoff"], description="fake")

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        self.requests.append(request)
        if not self.ok:
            return ToolResult(ok=False, tool=self.info().name, error="temporary failure")
        return ToolResult(ok=True, tool=self.info().name, output="inspection-complete")


class SequencePlanner(ActionPlanner):
    def __init__(self, intents):
        self.intents = list(intents)
        self.calls = 0

    def plan(self, context):
        self.calls += 1
        if not self.intents:
            return None
        return self.intents.pop(0)


def envelope() -> RuntimeEnvelope:
    return RuntimeEnvelope(
        session_id="conv_phase375_runtime",
        turn_id=1,
        provider="deepseek",
        backend="deepseek-chat",
        timestamp="2026-07-29T00:00:00Z",
        latency_target_ms=1500,
    )


def context(user_input="帮我检查 Julia Runtime 架构。"):
    return ContextCompiler(ROOT, policy=ContextPolicy(memory_limit=2)).compile(
        envelope(),
        user_input,
        conversation_context={},
        user_intent={"mode": "engineering_collaboration"},
    ).julia_context


def intent(**overrides):
    data = {
        "intent_type": "inspect_repository",
        "goal": "inspect Julia Runtime architecture",
        "target": "julia_agent",
        "risk_level": "low",
        "required_capability": "code_inspection",
        "reason": "Tony requested repository inspection",
        "confidence": 0.92,
    }
    data.update(overrides)
    return ActionIntent(**data)


def runtime_with(planner, *, fake=None, max_steps=5, max_failures=2, max_same=2):
    router = CapabilityRouter()
    fake = fake if fake is not None else FakeCapability()
    router.register(fake)
    runtime = CognitiveLoopRuntime(
        planner=planner,
        governance=ActionGovernanceLayer(),
        executor=ActionExecutor(router=router),
        reflector=ActionReflectionEngine(),
        continuation_policy=LoopContinuationPolicy(),
        max_steps=max_steps,
        max_failures=max_failures,
        max_consecutive_same_intent=max_same,
    )
    return runtime, fake


class Phase375CognitiveLoopRuntimeTests(unittest.TestCase):
    def test_tc_375_001_single_governed_loop(self):
        # TC-375-001
        runtime, fake = runtime_with(SequencePlanner([intent()]))

        result = runtime.run(context(), loop_id="tc375001")

        self.assertEqual(result.status, "complete")
        self.assertEqual(result.state.termination_reason, TerminationReason.GOAL_SATISFIED.value)
        self.assertEqual(len(result.trace.steps), 1)
        self.assertEqual(result.trace.steps[0].governance_decision, "allow")
        self.assertEqual(result.trace.steps[0].execution_status, "executed")
        self.assertEqual(result.trace.steps[0].reflection_status, "candidate")
        self.assertEqual(len(fake.requests), 1)

    def test_tc_375_002_ask_stops_loop(self):
        # TC-375-002
        runtime, fake = runtime_with(SequencePlanner([intent(intent_type="modify_file", required_capability="code_modification", risk_level="medium")]))

        result = runtime.run(context(), loop_id="tc375002")

        self.assertEqual(result.status, "ask_user")
        self.assertTrue(result.state.pending_confirmation)
        self.assertEqual(result.state.termination_reason, TerminationReason.ASK_USER.value)
        self.assertEqual(result.trace.steps[0].governance_decision, "ask")
        self.assertEqual(result.trace.steps[0].execution_status, "skipped")
        self.assertEqual(len(fake.requests), 0)

    def test_tc_375_003_reject_stops_loop(self):
        # TC-375-003
        runtime, fake = runtime_with(SequencePlanner([intent(target="identity", goal="change Julia identity", required_capability="destructive_operation", risk_level="high")]))

        result = runtime.run(context(), loop_id="tc375003")

        self.assertEqual(result.status, "aborted")
        self.assertEqual(result.state.termination_reason, TerminationReason.INVARIANT_VIOLATION.value)
        self.assertEqual(result.trace.steps[0].governance_decision, "reject")
        self.assertEqual(len(fake.requests), 0)

    def test_tc_375_004_step_limit(self):
        # TC-375-004
        class ContinuePolicy(LoopContinuationPolicy):
            def decide(self, **kwargs):
                from runtime.action.loop import ContinuationDecision
                return ContinuationDecision("CONTINUE", None)

        intents = [intent(goal=f"inspect area {i}") for i in range(5)]
        runtime, fake = runtime_with(SequencePlanner(intents), max_steps=2)
        runtime.continuation_policy = ContinuePolicy()

        result = runtime.run(context(), loop_id="tc375004")

        self.assertEqual(result.status, "paused")
        self.assertEqual(result.state.termination_reason, TerminationReason.STEP_LIMIT.value)
        self.assertEqual(len(result.trace.steps), 2)
        self.assertEqual(len(fake.requests), 2)

    def test_tc_375_005_failure_does_not_become_fact(self):
        # TC-375-005
        runtime, _ = runtime_with(SequencePlanner([intent()]), fake=FakeCapability(ok=False))

        result = runtime.run(context(), loop_id="tc375005")
        review = result.last_reflection

        self.assertEqual(result.status, "paused")
        self.assertEqual(result.state.termination_reason, TerminationReason.CAPABILITY_FAILURE.value)
        self.assertIsNotNone(review)
        self.assertIn(review.evidence.error_kind, {"execution_failed", "temporary_execution_failure", "permission_block"})
        self.assertIsNotNone(review.candidate)
        self.assertEqual(review.candidate.memory_type, "episodic")
        self.assertNotIn("project_fact", review.candidate.topics)
        self.assertNotIn("semantic_memory", review.candidate.topics)

    def test_tc_375_006_duplicate_intent_guard(self):
        # TC-375-006
        class ContinuePolicy(LoopContinuationPolicy):
            pass

        same = intent()
        runtime, fake = runtime_with(SequencePlanner([same, same, same]), max_same=1)
        runtime.continuation_policy = ContinuePolicy()
        # Force first successful action to continue so duplicate guard can evaluate second step.
        original = runtime.continuation_policy.decide
        calls = {"n": 0}
        def decide(**kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                from runtime.action.loop import ContinuationDecision
                return ContinuationDecision("CONTINUE", None)
            return original(**kwargs)
        runtime.continuation_policy.decide = decide

        result = runtime.run(context(), loop_id="tc375006")

        self.assertEqual(result.status, "paused")
        self.assertEqual(result.state.termination_reason, TerminationReason.DUPLICATE_INTENT.value)
        self.assertEqual(len(result.trace.steps), 2)
        self.assertEqual(len(fake.requests), 2)

    def test_tc_375_007_full_auditability(self):
        # TC-375-007
        runtime, _ = runtime_with(SequencePlanner([intent()]))

        result = runtime.run(context(), loop_id="tc375007")
        step = result.trace.steps[0].to_dict()

        for key in ["intent_trace", "governance_trace", "execution_trace", "reflection_trace", "continuation_trace"]:
            self.assertIn(key, step)
            self.assertIsNotNone(step[key])
        self.assertEqual(step["continuation_decision"], "COMPLETE")

    def test_tc_375_008_context_os_integration_mutates_between_steps(self):
        # TC-375-008
        class Adapter:
            def __init__(self):
                self.calls = 0
            def mutate_after_step(self, julia_context, step_trace):
                self.calls += 1
                return julia_context

        class ContinueOncePolicy(LoopContinuationPolicy):
            def __init__(self):
                self.calls = 0
            def decide(self, **kwargs):
                from runtime.action.loop import ContinuationDecision
                self.calls += 1
                if self.calls == 1:
                    return ContinuationDecision("CONTINUE", None)
                return ContinuationDecision("COMPLETE", TerminationReason.GOAL_SATISFIED.value)

        adapter = Adapter()
        runtime, _ = runtime_with(SequencePlanner([intent(goal="inspect one"), intent(goal="inspect two")]))
        runtime.continuation_policy = ContinueOncePolicy()
        runtime.context_mutation_adapter = adapter

        result = runtime.run(context(), loop_id="tc375008")

        self.assertEqual(result.status, "complete")
        self.assertEqual(len(result.trace.steps), 2)
        self.assertEqual(adapter.calls, 2)


if __name__ == "__main__":
    unittest.main()
