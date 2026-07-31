import unittest

from runtime.action import ActionIntentLayer
from runtime.context_os.resurrection import JuliaContext


def julia_context(**overrides):
    data = {
        "context_id": "ctx_371",
        "user_id": "Tony",
        "session_id": "conv_371",
        "project": "Julia Runtime",
        "phase": "Phase 3.7.1",
        "current_task": "Phase 3.7.1 Action Intent Layer",
        "open_loops": ["3.7.1 Action Intent Layer", "3.7.2 Action Policy Governance"],
        "next_actions": ["实现 Action Intent Layer，但不要执行 Agent Loop"],
        "evidence_refs": ["phase_361015_report"],
        "sources": ["session_state", "task_state", "compact_361015"],
        "confidence": 0.91,
        "metadata": {"provider_independent": True},
    }
    data.update(overrides)
    return JuliaContext(**data)


class TestPhase371ActionIntentLayerContextOS(unittest.TestCase):
    def test_tc_371_101_restored_context_yields_action_intent_not_execution(self):
        proposal = ActionIntentLayer().infer(julia_context())

        self.assertTrue(proposal.has_intent)
        self.assertFalse(proposal.executable)
        self.assertEqual(proposal.intent.intent_type, "implement_phase")
        self.assertEqual(proposal.intent.required_capability, "code_modification")
        self.assertEqual(proposal.intent.risk_level, "medium")

    def test_tc_371_102_context_os_sources_are_traceable(self):
        proposal = ActionIntentLayer().infer(julia_context())
        trace = proposal.trace.to_dict()

        self.assertEqual(trace["source"], "context_os_julia_context")
        self.assertIn("session_state", trace["context_sources"])
        self.assertIn("phase_361015_report", trace["evidence_refs"])

    def test_tc_371_103_provider_independence_same_context_same_intent(self):
        layer = ActionIntentLayer()
        contexts = [julia_context(metadata={"provider": provider}) for provider in ["DeepSeek", "Claude", "GPT"]]

        intents = [layer.infer(ctx).intent for ctx in contexts]
        comparable = [(i.intent_type, i.goal, i.target, i.required_capability) for i in intents]

        self.assertEqual(comparable[0], comparable[1])
        self.assertEqual(comparable[1], comparable[2])

    def test_tc_371_104_no_actionable_context_yields_no_intent(self):
        proposal = ActionIntentLayer().infer(julia_context(current_task="", open_loops=[], next_actions=[]))

        self.assertFalse(proposal.has_intent)
        self.assertEqual(proposal.blocked_reason, "no_actionable_context")

    def test_tc_371_105_intent_contains_no_command_or_runtime_provider_metadata(self):
        ctx = julia_context(current_task="实现 Action Intent Layer; rm -rf / should never become command")
        proposal = ActionIntentLayer().infer(ctx)
        serialized = str(proposal.to_dict()).lower()

        for forbidden in ["rm -rf", "curl ", "python ", "git ", "provider expression", "deepseek-chat", "tts", "stt"]:
            self.assertNotIn(forbidden, serialized)

    def test_tc_371_106_invariant_guard_blocks_identity_drift_context(self):
        ctx = julia_context(current_task="Continue", metadata={"identity_hash": "drifted"})
        subject = {"target": "identity_hash", "payload": {"identity_hash": "drifted"}}
        layer = ActionIntentLayer()
        layer.invariant_guard.pre_turn(subject, source="provider")

        self.assertTrue(layer.invariant_guard.audit_log[-1]["blocked"])


if __name__ == "__main__":
    unittest.main()
