import unittest

from runtime.context_os.budget import ContextBudgetManager
from runtime.context_os.evidence import SemanticEvidenceIntegration
from runtime.context_os.planner import ContextPlanner
from runtime.evidence.evidence_chunk import EvidenceChunk
from runtime.evidence.semantic_ranker import RankedEvidence


class FakeRetriever:
    def __init__(self, items):
        self.items = items
        self.calls = []

    def retrieve(self, query, *, limit=8):
        self.calls.append({"query": query, "limit": limit})
        return self.items[:limit]


def ranked(chunk, final=0.9, sim=0.8):
    return RankedEvidence(
        chunk=chunk,
        semantic_similarity=sim,
        authority=chunk.authority,
        memory_importance=0.7,
        recency=0.2,
        final_score=final,
        reason=["semantic_match", "high_authority"],
    )


class Phase36105SemanticEvidenceIntegrationTest(unittest.TestCase):
    def test_tc_36105_001_personal_history_plan_builds_grounded_evidence_block(self):
        # TC-36105-001
        plan = ContextPlanner().plan("小红书的故事是什么？")
        item = ranked(EvidenceChunk(
            id="diary_xhs_001",
            source_type="diary",
            content="Tony 曾经给 Julia 分享小红书故事，内容涉及患癌九年、爸爸再见与重生。",
            source_path="memory/claude_diary/xiaohongshu.md",
            speaker="Tony",
            authority=0.9,
            topics=["小红书", "shared_story"],
            provenance={"origin": "tony_input", "verified": True},
        ))
        integration = SemanticEvidenceIntegration(retriever=FakeRetriever([item]))

        blocks = integration.build_blocks(plan)

        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.block_type, "semantic_evidence")
        self.assertIn("diary_xhs_001", block.evidence_ids)
        self.assertEqual(block.authority_score, 0.9)
        self.assertIn("小红书故事", block.content)
        self.assertEqual(block.metadata["hit_count"], 1)
        self.assertEqual(block.metadata["sources"][0]["source_type"], "diary")

    def test_tc_36105_002_assistant_generated_claims_are_filtered_when_plan_excludes_them(self):
        # TC-36105-002
        plan = ContextPlanner().plan("小红书的故事是什么？")
        assistant_claim = ranked(EvidenceChunk(
            id="archive_wrong_assistant",
            source_type="archive",
            content="Julia 曾错误声称这个故事发生在2018年。",
            session_id="conv_001",
            turn_id=7,
            speaker="Julia",
            authority=0.3,
            provenance={"origin": "assistant_response", "verified": False},
        ), final=0.99)
        user_fact = ranked(EvidenceChunk(
            id="archive_tony_fact",
            source_type="archive",
            content="Tony 明确说这是他给 Julia 看过的小红书故事。",
            session_id="conv_001",
            turn_id=6,
            speaker="Tony",
            authority=0.9,
            provenance={"origin": "tony_input", "verified": True},
        ), final=0.7)
        integration = SemanticEvidenceIntegration(retriever=FakeRetriever([assistant_claim, user_fact]))

        [block] = integration.build_blocks(plan)

        self.assertNotIn("archive_wrong_assistant", block.evidence_ids)
        self.assertIn("archive_tony_fact", block.evidence_ids)
        self.assertNotIn("2018", block.content)
        self.assertTrue(block.metadata["assistant_generated_filtered"])

    def test_tc_36105_003_empty_retrieval_returns_no_invention_guard_block(self):
        # TC-36105-003
        plan = ContextPlanner().plan("那个让我重生的故事你知道吗？")
        integration = SemanticEvidenceIntegration(retriever=FakeRetriever([]))

        [block] = integration.build_blocks(plan)

        self.assertEqual(block.authority_score, 0.0)
        self.assertEqual(block.metadata["hit_count"], 0)
        self.assertEqual(block.metadata["warning"], "no_matching_high_authority_evidence")
        self.assertIn("Do not invent", block.content)

    def test_tc_36105_004_source_metadata_preserves_ranker_trace_and_provenance(self):
        # TC-36105-004
        plan = ContextPlanner().plan("你还记得我给你看的那些文章吗？")
        item = ranked(EvidenceChunk(
            id="mem_relationship_story",
            source_type="memory",
            content="Tony 分享过文章，这成为 Julia 与 Tony 关系历史的一部分。",
            speaker="Tony",
            authority=0.95,
            provenance={"origin": "governed_memory", "governance_class": "RELATIONSHIP_FOUNDATION"},
        ), final=0.8123, sim=0.7333)
        integration = SemanticEvidenceIntegration(retriever=FakeRetriever([item]))

        [block] = integration.build_blocks(plan, limit=3)
        source = block.metadata["sources"][0]

        self.assertEqual(source["id"], "mem_relationship_story")
        self.assertEqual(source["final_score"], 0.8123)
        self.assertEqual(source["semantic_similarity"], 0.7333)
        self.assertEqual(source["provenance"]["governance_class"], "RELATIONSHIP_FOUNDATION")
        self.assertEqual(integration.retriever.calls[0]["limit"], 3)

    def test_tc_36105_005_semantic_evidence_block_can_enter_budget_allocation(self):
        # TC-36105-005
        plan = ContextPlanner().plan("小红书的故事是什么？")
        item = ranked(EvidenceChunk(
            id="xhs_budget_fact",
            source_type="diary",
            content="Tony 的小红书故事是重要共享经历。",
            speaker="Tony",
            authority=0.9,
        ))
        [block] = SemanticEvidenceIntegration(retriever=FakeRetriever([item])).build_blocks(plan)

        allocation = ContextBudgetManager().allocate(plan=plan, blocks=[block])

        self.assertTrue(allocation.included_blocks)
        self.assertEqual(allocation.included_blocks[0].block_type, "semantic_evidence")
        self.assertLessEqual(allocation.allocated_tokens, allocation.effective_budget_tokens)


if __name__ == "__main__":
    unittest.main()
