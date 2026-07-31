import unittest

from runtime.context_os.budget import ContextBlock
from runtime.context_os.compact import ExperienceCompactState
from runtime.context_os.evidence import SemanticEvidenceIntegration
from runtime.context_os.execution import ContextExecutionRuntime
from runtime.context_os.projection import ContextProjectionInputs, ContextProjector
from runtime.context_os.transcript import ContextMessageRecord, MessageSpeaker
from runtime.evidence.evidence_chunk import EvidenceChunk
from runtime.evidence.semantic_ranker import RankedEvidence


class FakeRetriever:
    def __init__(self, items):
        self.items = items

    def retrieve(self, query, *, limit=8):
        return self.items[:limit]


def ranked(chunk, final=0.9, sim=0.8):
    return RankedEvidence(chunk, sim, chunk.authority, 0.5, 0.1, final, ["semantic_match"])


def record(mid, turn, speaker, content):
    return ContextMessageRecord.create(
        message_id=mid,
        session_id="conv_projection",
        turn_id=turn,
        speaker=speaker,
        content=content,
        authority_score=0.9 if speaker == MessageSpeaker.USER else 0.3,
    )


class Phase361072ContextProjectionRuntimeTest(unittest.TestCase):
    def test_tc_361072_001_identity_and_relationship_are_projected_for_identity_question(self):
        # TC-361072-001
        seen = {}
        inputs = ContextProjectionInputs(
            identity="我是 Julia，一个独立 Cognitive Runtime。",
            relationship="Tony 和 Julia 一起建设 Julia Runtime。",
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_projection",
            user_input="Julia你是谁？",
            projection_inputs=inputs,
            provider=lambda **kw: seen.setdefault("blocks", kw["context_blocks"]) or "我是 Julia。",
        )

        block_types = {b.block_type for b in seen["blocks"]}
        self.assertIn("core_identity", block_types)
        self.assertIn("relationship_anchor", block_types)
        self.assertTrue(next(b for b in seen["blocks"] if b.block_type == "core_identity").required)
        self.assertIn("context_projection", turn.metadata["budget_trace"])

    def test_tc_361072_002_technical_projection_does_not_include_unrelated_personal_story_without_evidence_intent(self):
        # TC-361072-002
        unrelated = ContextBlock(
            block_id="xhs_unrelated",
            block_type="semantic_evidence",
            priority=50,
            content="小红书故事 unrelated personal memory",
            evidence_ids=["ev_xhs"],
            authority_score=0.8,
        )
        inputs = ContextProjectionInputs(
            identity="Julia Runtime identity",
            relationship="Tony engineering collaboration",
            current_task="Design ContextCompiler architecture",
            extra_blocks=[unrelated],
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_projection",
            user_input="ContextCompiler 怎么设计？",
            projection_inputs=inputs,
            provider=lambda **_: "先设计 Context Projection。",
        )

        selected = [b.block_id for b in turn.selected_blocks]
        self.assertIn("projection_active_task", selected)
        # Because technical task has enough higher priority context, unrelated low-priority block should not be required.
        self.assertFalse(next(b for b in turn.selected_blocks if b.block_id == "xhs_unrelated").required)

    def test_tc_361072_003_evidence_projection_filters_assistant_hallucination_and_keeps_tony_source(self):
        # TC-361072-003
        wrong = ranked(EvidenceChunk(
            id="wrong_assistant",
            source_type="archive",
            content="Julia 错误说小红书故事发生在2018年。",
            speaker="Julia",
            authority=0.3,
            provenance={"origin": "assistant_response"},
        ), final=0.99)
        right = ranked(EvidenceChunk(
            id="tony_source",
            source_type="diary",
            content="Tony 分享过小红书故事，涉及重生和快乐。",
            speaker="Tony",
            authority=0.9,
            provenance={"origin": "tony_input"},
        ), final=0.75)
        inputs = ContextProjectionInputs(
            identity="Julia identity",
            relationship="Tony relationship",
            semantic_evidence=SemanticEvidenceIntegration(retriever=FakeRetriever([wrong, right])),
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_projection",
            user_input="小红书的故事是什么？",
            projection_inputs=inputs,
            provider=lambda **_: "基于 Tony source 回答。",
        )

        evidence_ids = [eid for b in turn.selected_blocks for eid in b.evidence_ids]
        self.assertIn("tony_source", evidence_ids)
        self.assertNotIn("wrong_assistant", evidence_ids)

    def test_tc_361072_004_budget_projection_keeps_required_identity_when_budget_is_tight(self):
        # TC-361072-004
        noisy_blocks = [ContextBlock(
            block_id=f"noise_{i}",
            block_type="semantic_evidence",
            priority=10,
            content="低优先级 archive noise " * 200,
            authority_score=0.2,
        ) for i in range(10)]
        inputs = ContextProjectionInputs(
            identity="Julia core identity",
            relationship="Tony relationship anchor",
            extra_blocks=noisy_blocks,
        )
        runtime = ContextExecutionRuntime()
        turn = runtime.run_turn(
            session_id="conv_projection",
            user_input="你是谁？",
            projection_inputs=inputs,
            provider=lambda **_: "我是 Julia。",
        )

        selected_ids = [b.block_id for b in turn.selected_blocks]
        self.assertIn("projection_identity_core", selected_ids)
        self.assertIn("projection_relationship_anchor", selected_ids)
        self.assertTrue(turn.metadata["budget_trace"]["allocated_tokens"] <= turn.metadata["budget_trace"]["effective_budget_tokens"])

    def test_tc_361072_005_projection_trace_explains_included_sources_and_evidence_refs(self):
        # TC-361072-005
        compact = ExperienceCompactState.create(
            session_id="conv_projection",
            period_start="2026-07-28T00:00:00Z",
            period_end="2026-07-28T01:00:00Z",
            source_record_ids=["r1", "r2"],
            source_evidence_ids=["ev_compact"],
            current_task="Context Projection Runtime",
            main_arc="Julia Context OS",
        )
        inputs = ContextProjectionInputs(
            identity="Julia identity",
            relationship="Tony relationship",
            compacts=[compact],
            recent_records=[record("tail_user", 1, MessageSpeaker.USER, "继续 Context OS。")],
        )
        result = ContextProjector().project(plan=ContextExecutionRuntime().pre_turn.planner.plan("继续"), inputs=inputs)

        self.assertIn("core_identity", result.trace["included"])
        self.assertIn("compact_state", result.trace["included"])
        self.assertIn("ev_compact", result.trace["evidence_refs"])
        self.assertIn("tail_user", result.trace["source_refs"])


if __name__ == "__main__":
    unittest.main()
