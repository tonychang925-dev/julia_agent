import unittest

from runtime.context_os.budget import ContextBlock
from runtime.context_os.conflict import ConflictItem, ContextConflictResolver
from runtime.context_os.execution import ContextExecutionRuntime


class Phase36108ContextConflictResolverTest(unittest.TestCase):
    def test_tc_36108_001_current_user_intent_beats_governed_memory(self):
        # TC-36108-001
        items = [
            ConflictItem("memory_pref", "Tony prefers engineering detail", "memory", 0.95, speaker="Tony", provenance="governed_memory", topic="response_style"),
            ConflictItem("current_intent", "Today Tony wants quiet support", "current", 1.0, speaker="Tony", provenance="current_user_intent", topic="response_style"),
        ]
        [resolution] = ContextConflictResolver().resolve_items(items)

        self.assertEqual(resolution.winner.item_id, "current_intent")
        self.assertEqual(resolution.rejected[0].item_id, "memory_pref")

    def test_tc_36108_002_tony_archive_fact_beats_assistant_historical_claim(self):
        # TC-36108-002
        tony = ContextBlock(
            block_id="tony_fact",
            block_type="semantic_evidence",
            priority=80,
            content="Tony said the Xiaohongshu story involved rebirth and happiness.",
            authority_score=0.9,
            metadata={"conflict_topic": "xiaohongshu_story", "speaker": "Tony", "provenance": "tony_input"},
        )
        julia = ContextBlock(
            block_id="julia_wrong",
            block_type="semantic_evidence",
            priority=95,
            content="Julia said the story happened in 2018.",
            authority_score=0.3,
            metadata={"conflict_topic": "xiaohongshu_story", "speaker": "Julia", "provenance": "assistant_response"},
        )
        blocks, [resolution] = ContextConflictResolver().resolve_blocks([julia, tony])

        self.assertEqual(resolution.winner.item_id, "tony_fact")
        self.assertTrue(next(b for b in blocks if b.block_id == "julia_wrong").included is False)
        self.assertEqual(next(b for b in blocks if b.block_id == "julia_wrong").exclusion_reason, "rejected_by_context_conflict_resolver")

    def test_tc_36108_003_diary_beats_assistant_claim_but_not_governed_memory(self):
        # TC-36108-003
        items = [
            ConflictItem("assistant", "assistant old answer", "archive", 0.3, speaker="Julia", provenance="assistant_response", topic="identity"),
            ConflictItem("diary", "diary imported identity", "diary", 0.8, provenance="imported_diary", topic="identity"),
            ConflictItem("memory", "governed identity memory", "memory", 0.95, provenance="governed_memory", topic="identity"),
        ]
        [resolution] = ContextConflictResolver().resolve_items(items)

        self.assertEqual(resolution.winner.item_id, "memory")
        self.assertEqual([x.item_id for x in resolution.rejected], ["diary", "assistant"])

    def test_tc_36108_004_pre_turn_records_conflict_resolution_trace_and_excludes_loser(self):
        # TC-36108-004
        winner = ContextBlock(
            block_id="current_fact",
            block_type="semantic_evidence",
            priority=60,
            content="Current Tony correction: use F5-TTS.",
            authority_score=1.0,
            metadata={"conflict_topic": "tts_engine", "speaker": "Tony", "provenance": "current_user_fact"},
        )
        loser = ContextBlock(
            block_id="old_assistant",
            block_type="semantic_evidence",
            priority=100,
            content="Old assistant answer: use ElevenLabs.",
            authority_score=0.3,
            metadata={"conflict_topic": "tts_engine", "speaker": "Julia", "provenance": "assistant_response"},
        )
        turn = ContextExecutionRuntime().run_turn(
            session_id="conv_conflict",
            user_input="为什么现在没有声音？",
            candidate_blocks=[loser, winner],
            provider=lambda **_: "使用当前 Tony 纠正后的 F5-TTS 方案。",
        )

        selected_ids = [b.block_id for b in turn.selected_blocks]
        self.assertIn("current_fact", selected_ids)
        self.assertNotIn("old_assistant", selected_ids)
        trace = turn.metadata["budget_trace"]["conflict_resolutions"]
        self.assertEqual(trace[0]["winner"]["item_id"], "current_fact")

    def test_tc_36108_005_unrelated_blocks_do_not_create_conflict(self):
        # TC-36108-005
        blocks = [
            ContextBlock("identity", "core_identity", 100, "Julia identity", authority_score=0.98, metadata={"conflict_topic": "identity"}),
            ContextBlock("task", "active_task", 90, "Context OS task", authority_score=0.8, metadata={"conflict_topic": "task"}),
        ]
        resolved, resolutions = ContextConflictResolver().resolve_blocks(blocks)

        self.assertEqual(len(resolutions), 0)
        self.assertTrue(all(b.included for b in resolved))


if __name__ == "__main__":
    unittest.main()
