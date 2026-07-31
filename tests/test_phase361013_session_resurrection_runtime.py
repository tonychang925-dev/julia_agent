import unittest

from runtime.context_os.compact import InMemoryCompactStore, StructuredCompactEngine
from runtime.context_os.resurrection import (
    InMemoryResurrectionSource,
    ResurrectionLoader,
    ResurrectionRequest,
    SessionResurrectionRuntime,
)
from runtime.context_os.state import JuliaSessionState, JuliaTaskState
from runtime.context_os.transcript import CognitiveRole, ContextMessageRecord


def record(mid, turn, content, role="task", speaker="USER", refs=None):
    return ContextMessageRecord.create(
        message_id=mid,
        session_id="conv_20260728",
        turn_id=turn,
        speaker=speaker,
        content=content,
        cognitive_role=role,
        source_refs=refs or [],
    )


def build_runtime():
    session = JuliaSessionState.create(
        session_id="conv_20260728",
        project="Julia Runtime",
        phase="Phase 3.6.10.13",
        architecture="Context OS",
        active_goals=["Restore yesterday's Julia cognitive state"],
    ).add_decision("Compact is Context Optimization, not Memory mutation.")
    task = JuliaTaskState.create(
        task_id="task_361013",
        session_id="conv_20260728",
        objective="Phase 3.6.10.13 Session Resurrection Runtime",
        status="active",
        progress=0.2,
        next_actions=["Implement Session Resurrection Runtime"],
    ).add_decision("Next phase after compact is Session Resurrection Runtime.")
    records = [
        record("msg_201", 1, "Phase 3.6.10.12 Compact 完成，下一步 Resurrection。", CognitiveRole.TASK, refs=["report_361012"]),
        record("msg_202", 2, "open loop: Compact Quality Evaluation。", CognitiveRole.TASK),
        record("msg_bad", 3, "Julia 猜测应该切换到无关任务。", CognitiveRole.EVIDENCE, speaker="ASSISTANT"),
        record("msg_203", 4, "继续 Phase 3.6.10.13 Session Resurrection Runtime。", CognitiveRole.TASK, refs=["phase_361013"]),
    ]
    compact = StructuredCompactEngine().compact(session_id="conv_20260728", records=[records[0], records[1], records[3]])
    store = InMemoryCompactStore()
    store.save(compact)
    source = InMemoryResurrectionSource(
        session_states={"conv_20260728": session},
        task_states={"task_361013": task},
        records=records,
        compact_store=store,
    )
    return SessionResurrectionRuntime(loader=ResurrectionLoader(source=source)), source


class TestPhase361013SessionResurrectionRuntime(unittest.TestCase):
    def test_tc_361013_001_cold_start_recovery_restores_project_phase_and_task(self):
        runtime, _ = build_runtime()
        request = ResurrectionRequest(user_id="Tony", session_id="conv_20260728", task_hint="continue Julia Runtime architecture")

        result = runtime.resurrect(request)

        self.assertTrue(result.restored)
        self.assertEqual(result.context.project, "Julia Runtime")
        self.assertEqual(result.context.phase, "Phase 3.6.10.13")
        self.assertEqual(result.context.current_task, "Phase 3.6.10.13 Session Resurrection Runtime")
        self.assertIn("session_state", result.validation.sources)
        self.assertIn("task_state", result.validation.sources)

    def test_tc_361013_002_task_continuity_answers_next_step_without_replanning(self):
        runtime, _ = build_runtime()

        result = runtime.resurrect(ResurrectionRequest(user_id="Tony", session_id="conv_20260728"))

        joined = "\n".join(result.context.next_actions + result.context.open_loops + [result.context.current_task])
        self.assertIn("Phase 3.6.10.13 Session Resurrection Runtime", joined)
        self.assertNotIn("重新规划", joined)

    def test_tc_361013_003_open_loop_recovery_merges_task_compact_and_tail(self):
        runtime, _ = build_runtime()

        result = runtime.resurrect(ResurrectionRequest(user_id="Tony", session_id="conv_20260728"))

        joined = "\n".join(result.context.open_loops + result.context.next_actions)
        self.assertIn("Compact Quality Evaluation", joined)
        self.assertIn("Implement Session Resurrection Runtime", joined)
        self.assertIn("下一步 Resurrection", joined)

    def test_tc_361013_004_evidence_integrity_filters_bad_assistant_tail_from_recovery(self):
        runtime, _ = build_runtime()

        result = runtime.resurrect(ResurrectionRequest(user_id="Tony", session_id="conv_20260728"))
        tail_ids = [r.message_id for r in result.context.recent_tail]

        self.assertNotIn("msg_bad", tail_ids)
        self.assertNotIn("msg_bad", result.context.evidence_refs)
        self.assertIn("msg_203", result.context.evidence_refs)

    def test_tc_361013_005_provider_independence_same_snapshot_reconstructs_same_context(self):
        runtime, _ = build_runtime()
        snapshot = runtime.loader.load(ResurrectionRequest(user_id="Tony", session_id="conv_20260728"))

        contexts = [runtime.reconstructor.reconstruct(snapshot) for _provider in ["DeepSeek", "Claude", "GPT"]]
        comparable = [
            (c.project, c.phase, c.current_task, c.open_loops, c.next_actions, c.evidence_refs)
            for c in contexts
        ]

        self.assertEqual(comparable[0], comparable[1])
        self.assertEqual(comparable[1], comparable[2])
        self.assertTrue(all(c.metadata["provider_independent"] for c in contexts))


if __name__ == "__main__":
    unittest.main()
