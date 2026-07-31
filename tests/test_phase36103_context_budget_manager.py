import unittest

from runtime.context_os.budget import ContextBlock, ContextBudgetManager
from runtime.context_os.planner import ContextPlanner


class TestPhase36103ContextBudgetManager(unittest.TestCase):
    def test_tc_36103_001_given_required_identity_blocks_when_budget_tight_then_required_blocks_are_kept(self):
        plan = ContextPlanner().plan("Julia你是谁？", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 900})
        blocks = [
            ContextBlock("id", "core_identity", 10, "identity" * 50, required=True, estimated_tokens=250),
            ContextBlock("rel", "relationship_anchor", 10, "relationship" * 50, required=True, estimated_tokens=250),
            ContextBlock("ev", "semantic_evidence", 50, "evidence" * 100, estimated_tokens=600, authority_score=0.95),
        ]

        allocation = ContextBudgetManager().allocate(plan=plan, blocks=blocks)
        included_ids = {b.block_id for b in allocation.included_blocks}

        self.assertIn("id", included_ids)
        self.assertIn("rel", included_ids)

    def test_tc_36103_002_given_personal_history_plan_when_budgeted_then_semantic_evidence_is_prioritized_over_recent_turns(self):
        plan = ContextPlanner().plan("小红书的故事是什么？", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 1200})
        blocks = [
            ContextBlock("id", "core_identity", 100, "identity", required=True, estimated_tokens=100),
            ContextBlock("rel", "relationship_anchor", 100, "relationship", required=True, estimated_tokens=100),
            ContextBlock("recent", "recent_turns", 40, "recent", estimated_tokens=700),
            ContextBlock("evidence", "semantic_evidence", 45, "xiaohongshu evidence", estimated_tokens=700, authority_score=0.9),
        ]

        allocation = ContextBudgetManager().allocate(plan=plan, blocks=blocks)
        included_ids = [b.block_id for b in allocation.included_blocks]
        excluded_ids = [b.block_id for b in allocation.excluded_blocks]

        self.assertIn("evidence", included_ids)
        self.assertIn("recent", excluded_ids)

    def test_tc_36103_003_given_excluded_runtime_trace_when_budgeted_then_runtime_trace_is_excluded_by_plan(self):
        plan = ContextPlanner().plan("我们现在在忙什么？", "engineering_collaboration")
        blocks = [
            ContextBlock("id", "core_identity", 100, "identity", required=True, estimated_tokens=100),
            ContextBlock("rel", "relationship_anchor", 100, "relationship", required=True, estimated_tokens=100),
            ContextBlock("task", "active_task", 100, "task", required=True, estimated_tokens=100),
            ContextBlock("trace", "runtime_trace", 999, "provider latency tts", estimated_tokens=10),
        ]

        allocation = ContextBudgetManager().allocate(plan=plan, blocks=blocks)

        self.assertNotIn("trace", {b.block_id for b in allocation.included_blocks})
        excluded = {b.block_id: b.exclusion_reason for b in allocation.excluded_blocks}
        self.assertEqual(excluded["trace"], "excluded_by_context_plan")

    def test_tc_36103_004_given_allocation_when_completed_then_trace_lists_included_and_excluded_blocks(self):
        plan = ContextPlanner().plan("我们现在在忙什么？", "engineering_collaboration")
        plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": 800})
        blocks = [
            ContextBlock("id", "core_identity", 100, "identity", required=True, estimated_tokens=100),
            ContextBlock("rel", "relationship_anchor", 100, "relationship", required=True, estimated_tokens=100),
            ContextBlock("task", "active_task", 100, "task", required=True, estimated_tokens=100),
            ContextBlock("recent", "recent_turns", 20, "recent", estimated_tokens=900),
        ]

        allocation = ContextBudgetManager().allocate(plan=plan, blocks=blocks)
        trace = allocation.to_trace()

        self.assertEqual(trace["plan_id"], plan.plan_id)
        self.assertIn("id", trace["included_blocks"])
        self.assertTrue(any(item["block_id"] == "recent" for item in trace["excluded_blocks"]))
        self.assertGreater(trace["budget_utilization"], 0)


if __name__ == "__main__":
    unittest.main()
