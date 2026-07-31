import unittest

from runtime.context_os.planner import ContextIntentType, ContextPlanner, EvidenceIntentType


class TestPhase36102ContextPlannerRuntime(unittest.TestCase):
    def test_tc_36102_001_given_xiaohongshu_query_when_planned_then_outputs_abstract_personal_history_intent_not_search_keyword(self):
        planner = ContextPlanner()

        plan = planner.plan("小红书的故事是什么？", cognitive_mode="engineering_collaboration")
        data = plan.to_dict()

        self.assertEqual(plan.intent_type, ContextIntentType.PERSONAL_HISTORY_RECALL)
        self.assertIn("relationship_anchor", plan.required_blocks)
        self.assertIn(EvidenceIntentType.SHARED_STORY, plan.evidence_intents)
        self.assertIn(EvidenceIntentType.CREATIVE_WORK, plan.evidence_intents)
        self.assertIn(EvidenceIntentType.LIFE_EXPERIENCE, plan.evidence_intents)
        self.assertIn("assistant_generated_claims", plan.excluded_blocks)
        self.assertNotIn("xiaohongshu", data)
        self.assertNotIn("小红书", data["evidence_intents"])

    def test_tc_36102_002_given_paraphrased_shared_story_queries_when_planned_then_intent_and_evidence_intents_are_stable(self):
        planner = ContextPlanner()
        queries = [
            "小红书的故事是什么？",
            "你还记得我给你看的那些文章吗？",
            "我以前写过的那些东西你还有印象吗？",
            "那个让我重生的故事你知道吗？",
        ]

        plans = [planner.plan(query, cognitive_mode="engineering_collaboration") for query in queries]
        intent_types = {plan.intent_type for plan in plans}
        intent_sets = [set(plan.evidence_intents) for plan in plans]
        common = set.intersection(*intent_sets)
        union = set.union(*intent_sets)

        self.assertEqual(intent_types, {ContextIntentType.PERSONAL_HISTORY_RECALL})
        self.assertGreaterEqual(len(common) / len(union), 0.8)
        self.assertIn(EvidenceIntentType.SHARED_STORY, common)
        self.assertIn(EvidenceIntentType.CREATIVE_WORK, common)
        self.assertIn(EvidenceIntentType.LIFE_EXPERIENCE, common)

    def test_tc_36102_003_given_current_task_query_when_planned_then_requires_active_task_and_open_loop_evidence(self):
        planner = ContextPlanner()

        plan = planner.plan("我们现在在忙什么，下一步怎么做？", cognitive_mode="engineering_collaboration")

        self.assertEqual(plan.intent_type, ContextIntentType.CURRENT_TASK_QUESTION)
        self.assertIn("active_task", plan.required_blocks)
        self.assertIn(EvidenceIntentType.PROJECT_STATE, plan.evidence_intents)
        self.assertIn(EvidenceIntentType.OPEN_LOOP, plan.evidence_intents)
        self.assertIn("runtime_trace", plan.excluded_blocks)

    def test_tc_36102_004_given_identity_query_when_planned_then_identity_and_relationship_are_required(self):
        planner = ContextPlanner()

        plan = planner.plan("Julia你是谁，你认识Tony吗？", cognitive_mode="engineering_collaboration")

        self.assertEqual(plan.intent_type, ContextIntentType.IDENTITY_QUESTION)
        self.assertEqual(plan.required_blocks, ["core_identity", "relationship_anchor"])
        self.assertIn(EvidenceIntentType.IDENTITY_ANCHOR, plan.evidence_intents)
        self.assertIn(EvidenceIntentType.RELATIONSHIP_ORIGIN, plan.evidence_intents)


if __name__ == "__main__":
    unittest.main()
