import unittest

from runtime.context_os.budget import ContextBlock
from runtime.context_os.execution import ContextExecutionRuntime, MutationType


class Phase361071ContextExecutionKernelTest(unittest.TestCase):
    def test_tc_361071_001_run_turn_reconstructs_context_before_provider(self):
        # TC-361071-001
        seen = {}

        def provider(*, user_input, context_blocks):
            seen["user_input"] = user_input
            seen["block_ids"] = [b.block_id for b in context_blocks]
            return "因为我们冻结了 Cognitive Ownership Principle。"

        blocks = [
            ContextBlock(
                block_id="identity_anchor",
                block_type="core_identity",
                priority=100,
                content="我是 Julia Runtime。",
                required=True,
                authority_score=0.95,
            ),
            ContextBlock(
                block_id="decision_ev",
                block_type="semantic_evidence",
                priority=90,
                content="Decision: Do not embed Claude Client.",
                evidence_ids=["ev_decision_001"],
                authority_score=0.9,
            ),
        ]

        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_exec",
            user_input="我们之前决定为什么不用方案A？",
            candidate_blocks=blocks,
            provider=provider,
            provider_request_id="req_001",
            provider_latency_ms=123,
        )

        self.assertEqual(seen["block_ids"], ["identity_anchor", "decision_ev"])
        self.assertEqual(turn.response, "因为我们冻结了 Cognitive Ownership Principle。")
        self.assertEqual(turn.provider_request_id, "req_001")
        self.assertIsNotNone(turn.trace_id)

    def test_tc_361071_002_post_turn_creates_task_and_open_loop_mutations(self):
        # TC-361071-002
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_exec",
            user_input="下一步怎么做？",
            candidate_blocks=[ContextBlock(
                block_id="task_state",
                block_type="active_task",
                priority=90,
                content="Current task: Context Execution Runtime",
                required=True,
                authority_score=0.8,
            )],
            provider=lambda **_: "先实现 Context Execution Kernel。",
        )

        mutation_types = {m.mutation_type for m in turn.mutations}
        self.assertIn(MutationType.TASK_PROGRESS_UPDATE, mutation_types)
        self.assertIn(MutationType.OPEN_LOOP_CREATED, mutation_types)

    def test_tc_361071_003_execution_honors_plan_exclusion_for_runtime_trace_blocks(self):
        # TC-361071-003
        included = ContextBlock(
            block_id="semantic_good",
            block_type="semantic_evidence",
            priority=90,
            content="Tony source evidence",
            evidence_ids=["ev_good"],
            authority_score=0.9,
        )
        excluded = ContextBlock(
            block_id="runtime_noise",
            block_type="runtime_trace",
            priority=99,
            content="provider latency details",
            authority_score=0.0,
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_exec",
            user_input="小红书的故事是什么？",
            candidate_blocks=[included, excluded],
            provider=lambda **_: "我会基于证据回答。",
        )

        selected_ids = [b.block_id for b in turn.selected_blocks]
        self.assertIn("semantic_good", selected_ids)
        self.assertNotIn("runtime_noise", selected_ids)
        self.assertIn("runtime_noise", turn.metadata["budget_trace"]["excluded_blocks"][0]["block_id"])

    def test_tc_361071_004_execution_trace_records_blocks_evidence_budget_quality_and_mutations(self):
        # TC-361071-004
        block = ContextBlock(
            block_id="ev_block",
            block_type="semantic_evidence",
            priority=90,
            content="Relevant evidence",
            evidence_ids=["ev_1"],
            authority_score=0.92,
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_exec",
            user_input="继续",
            candidate_blocks=[block],
            provider=lambda **_: "继续 Context Execution Runtime。",
        )

        data = turn.to_dict()
        self.assertIn("budget_trace", data["metadata"])
        self.assertEqual(data["selected_blocks"][0]["evidence_ids"], ["ev_1"])
        self.assertGreaterEqual(len(data["mutations"]), 1)
        self.assertIsNotNone(data["trace_id"])

    def test_tc_361071_005_high_risk_no_evidence_turn_creates_evidence_gap_mutation(self):
        # TC-361071-005
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_exec",
            user_input="小红书的故事是什么？",
            candidate_blocks=[],
            provider=lambda **_: "",
        )

        self.assertIn(MutationType.EVIDENCE_GAP_FOUND, {m.mutation_type for m in turn.mutations})


if __name__ == "__main__":
    unittest.main()
