import unittest

from runtime.context_os.budget import BudgetPressureLevel, CompactPreparationCandidate
from runtime.context_os.compact import CompactExecutionRequest, CompactExecutionStatus, StructuredCompactRuntime
from runtime.context_os.transcript import CognitiveRole, ContextMessageRecord


def record(mid, turn, content, role="task", refs=None):
    return ContextMessageRecord.create(
        message_id=mid,
        session_id="conv_compact_v2",
        turn_id=turn,
        speaker="USER",
        content=content,
        cognitive_role=role,
        source_refs=refs or [],
    )


def candidate(urgency=BudgetPressureLevel.HIGH, source_ids=None, reclaim=900):
    return CompactPreparationCandidate(
        candidate_id="compact_candidate_v2_001",
        reason="budget_pressure_prepare_only",
        source_block_ids=source_ids or ["r1", "r2", "r3", "tail"],
        estimated_reclaim_tokens=reclaim,
        urgency=urgency,
    )


class TestPhase361012StructuredCompactRuntimeV2(unittest.TestCase):
    def test_tc_361012_001_given_prepared_candidate_when_executed_then_compact_is_saved_with_trace(self):
        runtime = StructuredCompactRuntime()
        records = [
            record("r1", 1, "冻结决定：Budget Manager v2 只准备 compact。", CognitiveRole.DECISION),
            record("r2", 2, "下一步进入 Structured Compact Runtime。", CognitiveRole.TASK),
            record("r3", 3, "需要保留 source ids 和决策。", CognitiveRole.TASK),
        ]
        request = CompactExecutionRequest.create(session_id="conv_compact_v2", candidate=candidate())

        result = runtime.execute(request=request, records=records)

        self.assertEqual(result.status, CompactExecutionStatus.APPLIED)
        self.assertTrue(result.applied)
        self.assertIsNotNone(result.compact)
        self.assertEqual(result.trace.compacted_record_ids, ["r1", "r2", "r3"])
        self.assertEqual(runtime.store.get(result.compact.compact_id), result.compact)

    def test_tc_361012_002_given_preserve_tail_records_when_executed_then_tail_is_not_compacted(self):
        runtime = StructuredCompactRuntime()
        records = [
            record("r1", 1, "之前完成 Budget Pressure Measurement。", CognitiveRole.TASK),
            record("r2", 2, "决定：compact 必须 source-grounded。", CognitiveRole.DECISION),
            record("tail", 3, "当前最新 turn 必须保留在 context tail。", CognitiveRole.TASK),
        ]
        request = CompactExecutionRequest.create(
            session_id="conv_compact_v2",
            candidate=candidate(),
            preserve_tail_record_ids=["tail"],
        )

        result = runtime.execute(request=request, records=records)

        self.assertEqual(result.status, CompactExecutionStatus.APPLIED)
        self.assertEqual(result.trace.compacted_record_ids, ["r1", "r2"])
        self.assertEqual(result.trace.preserved_tail_record_ids, ["tail"])
        self.assertNotIn("tail", result.compact.source_record_ids)

    def test_tc_361012_003_given_low_pressure_candidate_when_executed_then_request_is_rejected(self):
        runtime = StructuredCompactRuntime()
        records = [record("r1", 1, "some history"), record("r2", 2, "more history")]
        request = CompactExecutionRequest.create(
            session_id="conv_compact_v2",
            candidate=candidate(urgency=BudgetPressureLevel.NORMAL),
        )

        result = runtime.execute(request=request, records=records)

        self.assertEqual(result.status, CompactExecutionStatus.REJECTED)
        self.assertEqual(result.trace.reason, "budget_pressure_not_high_enough")
        self.assertIsNone(result.compact)

    def test_tc_361012_004_given_same_idempotency_key_when_executed_twice_then_second_is_skipped(self):
        runtime = StructuredCompactRuntime()
        records = [
            record("r1", 1, "决定：第一次 compact 成功。", CognitiveRole.DECISION),
            record("r2", 2, "下一步验证 idempotency。", CognitiveRole.TASK),
        ]
        request = CompactExecutionRequest.create(
            session_id="conv_compact_v2",
            candidate=candidate(source_ids=["r1", "r2"]),
            idempotency_key="compact_once_key",
        )

        first = runtime.execute(request=request, records=records)
        second = runtime.execute(request=request, records=records)

        self.assertEqual(first.status, CompactExecutionStatus.APPLIED)
        self.assertEqual(second.status, CompactExecutionStatus.SKIPPED)
        self.assertEqual(second.trace.reason, "idempotency_key_already_applied")
        self.assertEqual(second.compact.compact_id, first.compact.compact_id)

    def test_tc_361012_005_given_tail_preservation_leaves_too_few_records_then_rejected_without_compact(self):
        runtime = StructuredCompactRuntime(min_records=2)
        records = [record("r1", 1, "only one compactable"), record("tail", 2, "latest tail")]
        request = CompactExecutionRequest.create(
            session_id="conv_compact_v2",
            candidate=candidate(source_ids=["r1", "tail"]),
            preserve_tail_record_ids=["tail"],
        )

        result = runtime.execute(request=request, records=records)

        self.assertEqual(result.status, CompactExecutionStatus.REJECTED)
        self.assertEqual(result.trace.reason, "insufficient_source_records_after_tail_preservation")
        self.assertEqual(result.trace.compacted_record_ids, ["r1"])
        self.assertIsNone(result.compact)


if __name__ == "__main__":
    unittest.main()
