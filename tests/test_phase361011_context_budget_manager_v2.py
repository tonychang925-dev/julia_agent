import unittest

from runtime.context_os.budget import BudgetPressureLevel, ContextBlock, ContextBudgetManagerV2
from runtime.context_os.planner import ContextPlanner


class TestPhase361011ContextBudgetManagerV2(unittest.TestCase):
    def test_tc_361011_001_given_tight_budget_when_allocating_then_recent_tail_is_preserved(self):
        plan = ContextPlanner().plan("继续当前任务", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 1000})
        blocks = [
            ContextBlock("identity", "core_identity", 90, "identity", required=True, estimated_tokens=120),
            ContextBlock("task", "active_task", 80, "task", required=True, estimated_tokens=120),
            ContextBlock("semantic", "semantic_evidence", 70, "evidence", estimated_tokens=700),
            ContextBlock("tail_old", "recent_turns", 10, "old", estimated_tokens=90, metadata={"tail_index": 1}),
            ContextBlock("tail_new", "recent_turns", 10, "new", estimated_tokens=90, metadata={"tail_index": 2}),
        ]

        result = ContextBudgetManagerV2().allocate(plan=plan, blocks=blocks)
        included = {block.block_id for block in result.included_blocks}

        self.assertIn("tail_old", included)
        self.assertIn("tail_new", included)
        self.assertEqual(result.preserve_tail_block_ids, ["tail_old", "tail_new"])

    def test_tc_361011_002_given_over_budget_projection_when_measured_then_pressure_requests_compact_preparation(self):
        plan = ContextPlanner().plan("总结很多历史证据", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 1200})
        blocks = [
            ContextBlock("identity", "core_identity", 90, "identity", required=True, estimated_tokens=200),
            ContextBlock("e1", "semantic_evidence", 80, "e1", estimated_tokens=600),
            ContextBlock("e2", "semantic_evidence", 70, "e2", estimated_tokens=600),
        ]

        pressure = ContextBudgetManagerV2().measure(plan=plan, blocks=blocks)

        self.assertIn(pressure.level, {BudgetPressureLevel.HIGH, BudgetPressureLevel.CRITICAL})
        self.assertTrue(pressure.should_prepare_compact)
        self.assertGreater(pressure.projected_utilization, pressure.utilization)

    def test_tc_361011_003_given_high_pressure_when_allocating_then_compact_candidate_is_prepare_only(self):
        plan = ContextPlanner().plan("回顾所有历史", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 1200})
        blocks = [
            ContextBlock("identity", "core_identity", 90, "identity", required=True, estimated_tokens=180),
            ContextBlock("tail", "recent_turns", 10, "latest", estimated_tokens=90, metadata={"tail_index": 9}),
            ContextBlock("e1", "semantic_evidence", 80, "e1", estimated_tokens=650),
            ContextBlock("e2", "semantic_evidence", 70, "e2", estimated_tokens=650),
        ]

        result = ContextBudgetManagerV2().allocate(plan=plan, blocks=blocks)
        trace = result.to_trace()

        self.assertTrue(result.compact_preparation_needed)
        self.assertFalse(trace["compact_executed"])
        self.assertEqual(result.compact_candidates[0].reason, "budget_pressure_prepare_only")
        self.assertGreaterEqual(result.compact_candidates[0].estimated_reclaim_tokens, 512)

    def test_tc_361011_004_given_low_pressure_when_allocating_then_no_compact_candidate_created(self):
        plan = ContextPlanner().plan("现在做什么", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 4000})
        blocks = [
            ContextBlock("identity", "core_identity", 90, "identity", required=True, estimated_tokens=100),
            ContextBlock("tail", "recent_turns", 10, "latest", estimated_tokens=90, metadata={"tail_index": 1}),
        ]

        result = ContextBudgetManagerV2().allocate(plan=plan, blocks=blocks)

        self.assertFalse(result.compact_preparation_needed)
        self.assertEqual(result.compact_candidates, [])


if __name__ == "__main__":
    unittest.main()
