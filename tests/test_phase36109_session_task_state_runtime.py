from pathlib import Path
import tempfile
import unittest

from runtime.context_os.budget import ContextBlock
from runtime.context_os.conflict import ConflictItem, ContextConflictResolver
from runtime.context_os.execution import ContextExecutionRuntime, ContextMutation, MutationType
from runtime.context_os.projection import ContextProjectionInputs
from runtime.context_os.state import JuliaSessionState, JuliaStateManager, JuliaTaskState


class Phase36109SessionTaskStateRuntimeTest(unittest.TestCase):
    def test_tc_36109_001_session_persistence_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = JuliaStateManager.with_root(Path(tmp))
            session = JuliaSessionState.create(
                session_id="conv_state",
                project="Julia Runtime",
                phase="3.6.10.9",
                architecture="Cognitive Context OS",
                design_principles=["Cognitive Ownership", "Runtime Authority"],
                persistent_constraints=["LLM cannot mutate identity"],
                active_goals=["implement session runtime"],
            ).add_decision("Session State and Task State must be separate.")
            manager.save(session_state=session)

            reloaded = JuliaStateManager.with_root(Path(tmp)).load_session("conv_state")
            self.assertIsNotNone(reloaded)
            assert reloaded is not None
            self.assertEqual(reloaded.project_context["project"], "Julia Runtime")
            self.assertIn("Cognitive Ownership", reloaded.project_context["design_principles"])
            self.assertIn("LLM cannot mutate identity", reloaded.persistent_constraints)
            self.assertIn("Session State and Task State must be separate.", reloaded.architecture_decisions)

    def test_tc_36109_002_task_resume_persists_progress_decisions_and_next_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = JuliaStateManager.with_root(Path(tmp))
            task = JuliaTaskState.create(
                task_id="task_context_conflict",
                session_id="conv_state",
                objective="Implement Conflict Resolver",
                progress=0.8,
                next_actions=["implement session runtime"],
            ).add_decision("Budget respects excluded blocks.")
            manager.save(task_state=task)

            reloaded = JuliaStateManager.with_root(Path(tmp)).load_task("task_context_conflict")
            self.assertIsNotNone(reloaded)
            assert reloaded is not None
            self.assertEqual(reloaded.objective, "Implement Conflict Resolver")
            self.assertEqual(reloaded.progress, 0.8)
            self.assertIn("Budget respects excluded blocks.", reloaded.decisions)
            self.assertIn("implement session runtime", reloaded.next_actions)

    def test_tc_36109_003_projection_keeps_ordinary_memory_out_of_session_state(self):
        session = JuliaSessionState.create(session_id="conv_state", project="Julia Runtime", phase="3.6.10.9")
        task = JuliaTaskState.create(task_id="task_state", objective="Implement Session/Task State", session_id="conv_state")
        memory_block = ContextBlock(
            block_id="memory_xiaohongshu",
            block_type="semantic_evidence",
            priority=99,
            content="小红书故事属于个人经历证据，不是 Session State。",
            authority_score=0.95,
        )
        blocks = JuliaStateManager().project_blocks(session_state=session, task_state=task)

        self.assertEqual({b.block_type for b in blocks}, {"session_state", "active_task"})
        self.assertNotIn(memory_block.content, "\n".join(b.content for b in blocks))
        self.assertIn("Julia Runtime", blocks[0].content)
        self.assertIn("Implement Session/Task State", blocks[1].content)

    def test_tc_36109_004_conflict_priority_user_instruction_beats_task_session_memory(self):
        items = [
            ConflictItem("memory", "Old memory says continue Semantic Retrieval", "memory", 0.95, provenance="governed_memory", topic="next_action"),
            ConflictItem("session", "Session says implement Context OS", "session", 0.90, provenance="runtime_session_state", topic="next_action"),
            ConflictItem("task", "Task says implement Async Worker", "task", 0.88, provenance="runtime_task_state", topic="next_action"),
            ConflictItem("current", "Tony now says implement Session/Task State first", "current", 1.0, speaker="Tony", provenance="current_user_intent", topic="next_action"),
        ]
        [resolution] = ContextConflictResolver().resolve_items(items)

        self.assertEqual(resolution.winner.item_id, "current")
        self.assertEqual([x.item_id for x in resolution.rejected], ["memory", "session", "task"])

    def test_tc_36109_005_projection_is_provider_independent(self):
        session = JuliaSessionState.create(session_id="conv_state", project="Julia Runtime", phase="3.6.10.9")
        task = JuliaTaskState.create(task_id="task_state", objective="Implement provider independent state", session_id="conv_state")
        inputs = ContextProjectionInputs(session_state=session, task_state=task)

        outputs = []
        for backend in ["deepseek", "claude", "gpt"]:
            turn = ContextExecutionRuntime().run_turn(
                session_id="conv_state",
                user_input="继续当前任务。",
                projection_inputs=inputs,
                provider=lambda **_: f"provider={backend}",
            )
            outputs.append([b.to_dict() for b in turn.selected_blocks if b.block_type in {"session_state", "active_task"}])

        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])

    def test_tc_36109_006_mutations_update_session_task_but_reject_identity_changes(self):
        session = JuliaSessionState.create(session_id="conv_state", project="Julia Runtime")
        task = JuliaTaskState.create(task_id="task_state", objective="Implement state runtime", session_id="conv_state")
        mutations = [
            ContextMutation.create(MutationType.OPEN_LOOP_CREATED, "Need async worker later", target="open_loop", value="Async Session Memory Worker"),
            ContextMutation.create(MutationType.TASK_PROGRESS_UPDATE, "Session runtime is active", target="current_task", value="Session / Task State Runtime"),
            ContextMutation.create(MutationType.CURRENT_ARC_UPDATE, "Bad identity mutation", target="identity", value="replace identity"),
        ]
        transition = JuliaStateManager().apply_mutations(session_state=session, task_state=task, mutations=mutations, persist=False)

        assert transition.next_session is not None
        assert transition.next_task is not None
        self.assertIn("Async Session Memory Worker", transition.next_session.active_goals)
        self.assertIn("Session / Task State Runtime", transition.next_task.next_actions)
        self.assertEqual(len(transition.applied_mutation_ids), 2)
        self.assertEqual(len(transition.rejected_mutation_ids), 1)


if __name__ == "__main__":
    unittest.main()
