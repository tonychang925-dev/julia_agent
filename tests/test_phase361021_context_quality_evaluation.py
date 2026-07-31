import unittest

from runtime.context_os.planner import ContextPlanner
from runtime.context_os.quality import ContextQualityEvaluator


def block(block_type, authority=0.0, tokens=100, evidence_ids=None, provenance_type="explicit_user", included=True, content="", conflict_topics=None):
    return {
        "block_type": block_type,
        "authority_score": authority,
        "estimated_tokens": tokens,
        "evidence_ids": evidence_ids or [],
        "provenance_type": provenance_type,
        "included": included,
        "content": content,
        "conflict_topics": conflict_topics or [],
    }


class TestPhase361021ContextQualityEvaluation(unittest.TestCase):
    def test_tc_361021_001_given_identity_plan_with_identity_and_relationship_blocks_then_quality_gate_passes(self):
        plan = ContextPlanner().plan("Julia你是谁，你认识Tony吗？", "engineering_collaboration")
        quality = ContextQualityEvaluator().evaluate(
            plan=plan,
            blocks=[
                block("core_identity", tokens=300),
                block("relationship_anchor", tokens=300),
                block("semantic_evidence", authority=0.95, evidence_ids=["mem_identity"]),
            ],
        )

        self.assertTrue(quality.pass_gate)
        self.assertEqual(quality.identity_coverage, 1.0)
        self.assertEqual(quality.relationship_coverage, 1.0)
        self.assertGreaterEqual(quality.evidence_confidence, 0.9)
        self.assertLess(quality.hallucination_risk, 0.5)

    def test_tc_361021_002_given_historical_query_with_only_assistant_claims_then_quality_flags_high_hallucination_risk(self):
        plan = ContextPlanner().plan("小红书的故事是什么？", "engineering_collaboration")
        quality = ContextQualityEvaluator().evaluate(
            plan=plan,
            blocks=[
                block("core_identity", tokens=200),
                block("relationship_anchor", tokens=200),
                block("semantic_evidence", authority=0.3, evidence_ids=["assistant_wrong_1"], provenance_type="assistant_response"),
                block("semantic_evidence", authority=0.3, evidence_ids=["assistant_wrong_2"], provenance_type="assistant_response"),
            ],
        )

        self.assertFalse(quality.pass_gate)
        self.assertGreaterEqual(quality.hallucination_risk, 0.85)
        self.assertGreater(quality.assistant_generated_ratio, 0.5)
        self.assertIn("assistant_generated_evidence_dominates", quality.warnings)
        self.assertIn("highest_authority_is_low_assistant_or_inference_only", quality.warnings)

    def test_tc_361021_003_given_context_over_budget_then_quality_warns_budget_utilization_too_high(self):
        plan = ContextPlanner().plan("我们现在在忙什么？", "engineering_collaboration")
        quality = ContextQualityEvaluator().evaluate(
            plan=plan,
            blocks=[
                block("core_identity", tokens=500),
                block("relationship_anchor", tokens=500),
                block("active_task", tokens=500),
                block("recent_turns", authority=0.9, tokens=12000, evidence_ids=["recent"]),
            ],
        )

        self.assertTrue(quality.pass_gate)
        self.assertGreater(quality.budget_utilization, 0.92)
        self.assertIn("budget_utilization_too_high", quality.warnings)

    def test_tc_361021_004_given_conflicting_evidence_blocks_then_quality_reports_conflict_count(self):
        plan = ContextPlanner().plan("小红书的故事是什么？", "engineering_collaboration")
        quality = ContextQualityEvaluator().evaluate(
            plan=plan,
            blocks=[
                block("core_identity", tokens=200),
                block("relationship_anchor", tokens=200),
                block("semantic_evidence", authority=0.9, evidence_ids=["tony_story"], content="Tony shared Xiaohongshu posts", conflict_topics=["story_origin"]),
                block("semantic_evidence", authority=0.3, evidence_ids=["julia_guess"], provenance_type="assistant_response", content="Julia guessed a different story", conflict_topics=["story_origin"]),
            ],
        )

        self.assertEqual(quality.conflict_count, 1)
        self.assertIn("context_conflict_detected", quality.warnings)
        self.assertGreaterEqual(quality.highest_authority, 0.9)


if __name__ == "__main__":
    unittest.main()
