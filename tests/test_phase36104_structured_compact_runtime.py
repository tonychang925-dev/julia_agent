import unittest

from runtime.context_os.compact import InMemoryCompactStore, StructuredCompactEngine
from runtime.context_os.transcript import CognitiveRole, ContextMessageRecord, ProvenanceType


def record(mid, turn, content, role="task", speaker="USER", authority=None, refs=None):
    kwargs = {}
    if authority is not None:
        kwargs["authority_score"] = authority
    return ContextMessageRecord.create(
        message_id=mid,
        session_id="conv_compact_001",
        turn_id=turn,
        speaker=speaker,
        content=content,
        cognitive_role=role,
        source_refs=refs or [],
        **kwargs,
    )


class TestPhase36104StructuredCompactRuntime(unittest.TestCase):
    def test_tc_36104_001_given_records_when_compacted_then_outputs_structured_compact_with_source_ids(self):
        records = [
            record("r1", 1, "Tony 决定 Phase 3.6.10 采用 Julia Context OS。", CognitiveRole.DECISION),
            record("r2", 2, "下一步实现 Structured Compact Runtime。", CognitiveRole.TASK),
        ]

        compact = StructuredCompactEngine().compact(session_id="conv_compact_001", records=records)

        self.assertTrue(compact.compact_id.startswith("ctx_compact_"))
        self.assertEqual(compact.source_record_ids, ["r1", "r2"])
        self.assertEqual(len(compact.decisions), 1)
        self.assertIn("Structured Compact Runtime", compact.current_task)
        self.assertEqual(compact.schema_version, "experience_compact_state.v1")

    def test_tc_36104_002_given_decisions_failures_and_open_loops_when_compacted_then_preserves_them_in_schema(self):
        records = [
            record("r1", 1, "冻结决定：Claude Client 是参考架构，不是依赖。", CognitiveRole.DECISION),
            record("r2", 2, "之前小红书故事回答不对，属于胡编问题。", CognitiveRole.TASK),
            record("r3", 3, "下一步继续实现 Context Budget Manager。", CognitiveRole.TASK),
        ]

        compact = StructuredCompactEngine().compact(session_id="conv_compact_001", records=records)

        self.assertEqual(len(compact.decisions), 1)
        self.assertEqual(len(compact.known_failures), 1)
        self.assertTrue(any("下一步" in item for item in compact.open_loops))
        self.assertTrue(any("Context Budget Manager" in item for item in compact.next_actions))

    def test_tc_36104_003_given_source_refs_when_compacted_then_source_evidence_ids_are_traceable(self):
        records = [
            record("r1", 1, "Tony 提到小红书文章。", CognitiveRole.EVIDENCE, refs=["evidence_xhs_001"]),
            record("r2", 2, "Julia 不能把 assistant_response 当高权威事实。", CognitiveRole.DECISION, refs=["evidence_policy_001"]),
        ]

        compact = StructuredCompactEngine().compact(session_id="conv_compact_001", records=records)

        self.assertEqual(compact.source_evidence_ids, ["evidence_xhs_001", "evidence_policy_001"])
        self.assertIn("r1", compact.to_context_block_text())
        self.assertIn("r2", compact.to_context_block_text())

    def test_tc_36104_004_given_assistant_heavy_records_when_compacted_then_confidence_stays_lower_than_user_grounded_compact(self):
        user_records = [record("u1", 1, "Tony 明确说 Julia 正在实现 Context OS。", CognitiveRole.TASK)]
        assistant_records = [
            record("a1", 1, "Julia 猜测某个故事发生在2018年。", CognitiveRole.EVIDENCE, speaker="ASSISTANT"),
            record("a2", 2, "Julia 又补充了未经证实的细节。", CognitiveRole.EVIDENCE, speaker="ASSISTANT"),
        ]

        user_compact = StructuredCompactEngine().compact(session_id="conv_compact_001", records=user_records)
        assistant_compact = StructuredCompactEngine().compact(session_id="conv_compact_001", records=assistant_records)

        self.assertGreater(user_compact.confidence, assistant_compact.confidence)
        self.assertEqual(assistant_compact.metadata["assistant_record_count"], 2)

    def test_tc_36104_005_given_compact_when_saved_then_store_can_retrieve_by_id_and_session(self):
        compact = StructuredCompactEngine().compact(
            session_id="conv_compact_001",
            records=[record("r1", 1, "下一步继续 Semantic Evidence Integration。", CognitiveRole.TASK)],
        )
        store = InMemoryCompactStore()

        store.save(compact)

        self.assertEqual(store.get(compact.compact_id), compact)
        self.assertEqual(store.list_for_session("conv_compact_001"), [compact])


if __name__ == "__main__":
    unittest.main()
