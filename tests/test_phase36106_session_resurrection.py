import unittest

from runtime.context_os.compact import CompactDecision, ExperienceCompactState
from runtime.context_os.session import SessionResurrectionEngine, SessionSnapshot
from runtime.context_os.transcript import ContextMessageRecord, MessageSpeaker


def record(mid, turn, speaker, content):
    return ContextMessageRecord.create(
        message_id=mid,
        session_id="conv_prev",
        turn_id=turn,
        speaker=speaker,
        content=content,
        topics=["Julia Runtime"],
    )


def compact():
    return ExperienceCompactState.create(
        session_id="conv_prev",
        period_start="2026-07-28T00:00:00Z",
        period_end="2026-07-28T01:00:00Z",
        source_record_ids=["u1", "a1", "u2"],
        source_evidence_ids=["ev_ctx_os"],
        title="Julia Context OS Work Session",
        session_goal="Build Context OS",
        current_task="Phase 3.6.10 Session Resurrection",
        main_arc="Julia Context OS development",
        decisions=[CompactDecision(topic="Context OS", decision="Use compact boundary plus active tail", source_record_ids=["u2"])],
        open_loops=["Implement Async Session Memory Worker"],
        next_actions=["Run resurrection tests"],
        relationship_development=["Tony and Julia continue Context OS architecture work"],
        confidence=0.82,
    )


class Phase36106SessionResurrectionTest(unittest.TestCase):
    def test_tc_36106_001_snapshot_preserves_compact_ids_tail_and_open_loops(self):
        # TC-36106-001
        c = compact()
        records = [record(f"m{i}", i, MessageSpeaker.USER, f"turn {i}") for i in range(20)]
        snapshot = SessionResurrectionEngine(max_tail_records=5).create_snapshot(
            source_session_id="conv_prev",
            compacts=[c],
            preserved_records=records,
        )

        self.assertEqual(snapshot.source_session_id, "conv_prev")
        self.assertEqual(snapshot.compact_ids, [c.compact_id])
        self.assertEqual(snapshot.preserved_record_ids, [f"m{i}" for i in range(15, 20)])
        self.assertIn("Implement Async Session Memory Worker", snapshot.open_loops)

    def test_tc_36106_002_build_blocks_reconstructs_compact_open_loops_and_tail(self):
        # TC-36106-002
        c = compact()
        records = [
            record("u1", 1, MessageSpeaker.USER, "我们在做 Context OS。"),
            record("a1", 1, MessageSpeaker.ASSISTANT, "下一步是 resurrection。"),
        ]
        engine = SessionResurrectionEngine()
        snapshot = engine.create_snapshot(source_session_id="conv_prev", compacts=[c], preserved_records=records)

        blocks = engine.build_blocks(snapshot=snapshot, compacts=[c], preserved_records=records)
        types = {b.block_type for b in blocks}

        self.assertIn("compact_state", types)
        self.assertIn("recent_turns", types)
        self.assertIn("open_loops", types)
        self.assertTrue(next(b for b in blocks if b.block_type == "compact_state").required)
        self.assertIn("Phase 3.6.10 Session Resurrection", next(b for b in blocks if b.block_type == "open_loops").content)

    def test_tc_36106_003_snapshot_validates_required_identity(self):
        # TC-36106-003
        with self.assertRaises(ValueError):
            SessionSnapshot(snapshot_id="", source_session_id="conv_prev")
        with self.assertRaises(ValueError):
            SessionSnapshot(snapshot_id="snap", source_session_id="")

    def test_tc_36106_004_missing_compact_or_tail_records_are_ignored_safely(self):
        # TC-36106-004
        snapshot = SessionSnapshot.create(
            source_session_id="conv_prev",
            compact_ids=["missing_compact"],
            preserved_record_ids=["missing_record"],
            open_loops=["Continue Context OS"],
        )
        blocks = SessionResurrectionEngine().build_blocks(snapshot=snapshot, compacts=[], preserved_records=[])

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type, "open_loops")
        self.assertIn("Continue Context OS", blocks[0].content)


if __name__ == "__main__":
    unittest.main()
