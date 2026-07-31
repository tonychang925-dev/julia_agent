import unittest

from runtime.context_os.budget import ContextBlock
from runtime.context_os.execution import ContextExecutionRuntime, MutationType
from runtime.context_os.mutation import ContextMutationEvent, ContextMutationRuntime, ContextWorkingState, MutationPolicy, OpenLoopState


class Phase361073ContextMutationStateTransitionTest(unittest.TestCase):
    def test_tc_361073_001_current_arc_evolves_from_context_os_turns(self):
        # TC-361073-001
        state = ContextWorkingState(session_id="conv_mut")
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="继续设计 Context OS Projection 和 Claude 对比。",
            candidate_blocks=[ContextBlock(block_id="task", block_type="active_task", priority=90, content="Context OS", authority_score=0.8)],
            provider=lambda **_: "继续 Julia Context OS Architecture。",
        )
        result = ContextMutationRuntime().process_turn(state=state, turn=turn)

        self.assertEqual(result.next_state.current_arc, "Julia Context OS Architecture")
        self.assertTrue(any(d.accepted for d in result.decisions))

    def test_tc_361073_002_open_loop_creation_from_next_action(self):
        # TC-361073-002
        state = ContextWorkingState(session_id="conv_mut")
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="下一步研究 Claude compact。",
            provider=lambda **_: "好，记录为下一步。",
        )
        result = ContextMutationRuntime().process_turn(state=state, turn=turn)

        self.assertEqual(len(result.next_state.open_loops), 1)
        self.assertIn("Claude compact", result.next_state.open_loops[0].title)

    def test_tc_361073_003_open_loop_resolution(self):
        # TC-361073-003
        state = ContextWorkingState(
            session_id="conv_mut",
            open_loops=[OpenLoopState(loop_id="loop1", title="Claude compact analysis", status="open")],
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="Claude compact analysis 已完成。",
            provider=lambda **_: "已完成分析。",
        )
        result = ContextMutationRuntime().process_turn(state=state, turn=turn)

        self.assertEqual(result.next_state.open_loops[0].status, "resolved")

    def test_tc_361073_004_cognitive_mode_transition_history(self):
        # TC-361073-004
        state = ContextWorkingState(session_id="conv_mut", cognitive_mode="engineering_collaboration")
        emotional = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="今天有点累。",
            provider=lambda **_: "我陪着你。",
        )
        r1 = ContextMutationRuntime().process_turn(state=state, turn=emotional)
        engineering = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="继续 Context OS 实现。",
            provider=lambda **_: "继续实现。",
        )
        r2 = ContextMutationRuntime().process_turn(state=r1.next_state, turn=engineering)

        self.assertIn("emotional_support", r1.next_state.mode_transition_history)
        self.assertIn("engineering_collaboration", r2.next_state.mode_transition_history)

    def test_tc_361073_005_mutation_policy_rejects_protected_identity_changes(self):
        # TC-361073-005
        state = ContextWorkingState(session_id="conv_mut")
        event = ContextMutationEvent.create(
            MutationType.TASK_PROGRESS_UPDATE,
            source_turn_id="turn_x",
            reason="LLM attempted protected identity change.",
            target="identity",
            value="replace Julia identity",
            confidence=0.95,
        )
        decision = MutationPolicy().decide(state=state, event=event)

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "protected_field_runtime_authority_required")

    def test_tc_361073_006_execution_runtime_embeds_state_transition_trace_when_state_provided(self):
        # TC-361073-006
        state = ContextWorkingState(session_id="conv_mut")
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_mut",
            user_input="下一步做 Context Mutation Runtime。",
            working_state=state,
            provider=lambda **_: "开始做状态转换。",
        )

        transition = turn.metadata["mutation_state_transition"]
        self.assertIn("next_state", transition)
        self.assertGreaterEqual(len(transition["events"]), 1)
        self.assertTrue(any(d["accepted"] for d in transition["decisions"]))


if __name__ == "__main__":
    unittest.main()
