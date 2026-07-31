import unittest

from runtime.context_os.transcript import (
    CognitiveRole,
    MessageLifecycleState,
    MessageSpeaker,
    ProvenanceType,
    TranscriptLifecycleManager,
)
from runtime.context_os.transcript.message_record import ContextMessageRecord


class TestPhase36101ConversationTruthLayer(unittest.TestCase):
    def test_tc_36101_001_given_one_dialogue_turn_when_ingested_then_creates_user_and_assistant_context_records(self):
        manager = TranscriptLifecycleManager()

        records = manager.ingest_turn(
            session_id="conv_truth_001",
            turn_id=1,
            user="Tony 明确说 Julia Runtime 正在进入 Context OS 阶段。",
            assistant="我会继续推进 Context OS。",
            topics=["Julia Runtime", "Context OS"],
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].speaker, MessageSpeaker.USER)
        self.assertEqual(records[0].provenance_type, ProvenanceType.EXPLICIT_USER)
        self.assertEqual(records[0].authority_score, 0.9)
        self.assertEqual(records[0].lifecycle_state, MessageLifecycleState.ACTIVE)
        self.assertEqual(records[1].speaker, MessageSpeaker.ASSISTANT)
        self.assertEqual(records[1].provenance_type, ProvenanceType.ASSISTANT_RESPONSE)
        self.assertEqual(records[1].authority_score, 0.3)

    def test_tc_36101_002_given_assistant_error_fact_when_recorded_then_low_authority_cannot_equal_user_source(self):
        user_record = ContextMessageRecord.create(
            message_id="user_fact",
            session_id="conv_truth_002",
            turn_id=1,
            speaker="USER",
            content="Tony: 我给你看过小红书文章。",
            cognitive_role="evidence",
        )
        assistant_record = ContextMessageRecord.create(
            message_id="assistant_guess",
            session_id="conv_truth_002",
            turn_id=2,
            speaker="ASSISTANT",
            content="Julia: 我猜那个故事发生在去年夏天。",
            cognitive_role="evidence",
        )

        self.assertEqual(user_record.authority_score, 0.9)
        self.assertEqual(assistant_record.authority_score, 0.3)
        self.assertLess(assistant_record.authority_score, user_record.authority_score)
        self.assertEqual(assistant_record.provenance_type, ProvenanceType.ASSISTANT_RESPONSE)

    def test_tc_36101_003_given_ten_turns_when_compact_boundary_applied_then_old_records_compressed_and_tail_active(self):
        manager = TranscriptLifecycleManager()
        for turn_id in range(1, 11):
            manager.ingest_turn(
                session_id="conv_truth_003",
                turn_id=turn_id,
                user=f"user turn {turn_id}",
                assistant=f"assistant turn {turn_id}",
            )

        boundary = manager.apply_compact_boundary(
            session_id="conv_truth_003",
            compress_before_turn=9,
            preserve_last_turns=2,
            compact_id="compact_001",
        )
        state_by_turn = {}
        for record in manager.records:
            if record.session_id == "conv_truth_003":
                state_by_turn.setdefault(record.turn_id, set()).add(record.lifecycle_state)

        for turn_id in range(1, 9):
            self.assertEqual(state_by_turn[turn_id], {MessageLifecycleState.COMPRESSED})
        for turn_id in (9, 10):
            self.assertEqual(state_by_turn[turn_id], {MessageLifecycleState.ACTIVE})
        self.assertEqual(len(boundary.summarized_record_ids), 16)
        self.assertEqual(len(boundary.preserved_record_ids), 4)
        self.assertEqual(boundary.compact_id, "compact_001")

    def test_tc_36101_004_given_context_roles_when_state_built_then_reconstructs_identity_relationship_task_and_open_loop(self):
        manager = TranscriptLifecycleManager()
        manager.records.extend(
            [
                ContextMessageRecord.create(
                    message_id="identity_1",
                    session_id="conv_truth_004",
                    turn_id=1,
                    speaker="USER",
                    content="Julia 是独立 Cognitive Runtime。",
                    cognitive_role=CognitiveRole.IDENTITY,
                ),
                ContextMessageRecord.create(
                    message_id="relationship_1",
                    session_id="conv_truth_004",
                    turn_id=2,
                    speaker="USER",
                    content="Tony 是 Julia Runtime 的长期共同建设者。",
                    cognitive_role=CognitiveRole.RELATIONSHIP,
                ),
                ContextMessageRecord.create(
                    message_id="task_1",
                    session_id="conv_truth_004",
                    turn_id=3,
                    speaker="USER",
                    content="当前任务是实现 Conversation Truth Layer。",
                    cognitive_role=CognitiveRole.TASK,
                ),
                ContextMessageRecord.create(
                    message_id="decision_1",
                    session_id="conv_truth_004",
                    turn_id=4,
                    speaker="USER",
                    content="下一步继续 Context Planner + Context Quality。",
                    cognitive_role=CognitiveRole.DECISION,
                ),
            ]
        )

        state = manager.build_context_state("conv_truth_004")
        summary = state.reconstruct_summary()

        self.assertEqual(summary["identity"], ["Julia 是独立 Cognitive Runtime。"])
        self.assertEqual(summary["relationship"], ["Tony 是 Julia Runtime 的长期共同建设者。"])
        self.assertEqual(summary["task"], ["当前任务是实现 Conversation Truth Layer。"])
        self.assertEqual(summary["open_loop"], ["下一步继续 Context Planner + Context Quality。"])


if __name__ == "__main__":
    unittest.main()
