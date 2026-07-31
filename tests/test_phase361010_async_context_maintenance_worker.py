import time
import unittest

from runtime.context_os import (
    AsyncContextMaintenanceRuntime,
    JuliaSessionState,
    JuliaStateManager,
    JuliaTaskState,
    ProposalType,
    WorkerEvent,
)
from runtime.context_os.proposal import ProposalValidator, StateProposal
from runtime.context_os.worker import MaintenanceJob


class Phase361010AsyncContextMaintenanceWorkerTest(unittest.TestCase):
    def test_tc_361010_001_async_isolation_enqueue_does_not_run_maintenance(self):
        runtime = AsyncContextMaintenanceRuntime()
        started = time.perf_counter()
        runtime.submit_turn_completed(
            source_turn_id="turn_voice_1",
            payload={"user": "Phase 3.6.10.10 Context OS 完成后再维护", "turn_count": 1000},
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        self.assertLess(elapsed_ms, 25)
        self.assertEqual(len(runtime.queue), 1)
        result = runtime.run_once()
        self.assertGreaterEqual(len(result.proposals), 1)

    def test_tc_361010_002_memory_proposal_is_candidate_only_not_direct_write(self):
        runtime = AsyncContextMaintenanceRuntime()
        runtime.submit_turn_completed(
            source_turn_id="turn_1001",
            payload={"assistant": "Phase 3.6.10.9 milestone 完成：Julia Context OS 是长期项目。"},
        )
        result = runtime.run_once()

        memory = [p for p in result.proposals if p.proposal_type == ProposalType.MEMORY_CANDIDATE]
        self.assertEqual(len(memory), 1)
        self.assertIn(memory[0], result.validation.candidate_only)
        with self.assertRaises(ValueError):
            memory[0].to_mutation()

    def test_tc_361010_003_session_proposal_detects_long_lived_architecture_change(self):
        runtime = AsyncContextMaintenanceRuntime()
        runtime.submit_turn_completed(
            source_turn_id="turn_arch",
            payload={"user": "Phase 3.6.10 Context OS State Ownership 状态归属成为当前架构。"},
        )
        result = runtime.run_once()

        proposals = [p for p in result.proposals if p.proposal_type == ProposalType.SESSION_STATE_UPDATE]
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].metadata["session_update"]["current_architecture"], "Julia Context OS")
        self.assertIn(proposals[0], result.validation.mutation_ready)

    def test_tc_361010_004_task_evolution_generates_open_loop_resolved_update(self):
        runtime = AsyncContextMaintenanceRuntime()
        runtime.submit_turn_completed(
            source_turn_id="turn_task",
            payload={"assistant": "Conflict Resolver completed，open_loop resolved，next action 是 Session State Runtime。"},
        )
        result = runtime.run_once()

        task = [p for p in result.validation.mutation_ready if p.proposal_type == ProposalType.TASK_STATE_UPDATE]
        self.assertEqual(len(task), 1)
        self.assertEqual(task[0].payload["progress"], 1.0)
        self.assertEqual(task[0].metadata["open_loop"], "resolved")

    def test_tc_361010_005_authority_protection_rejects_persona_relationship_mutation(self):
        proposals = [
            StateProposal.create(
                ProposalType.SESSION_STATE_UPDATE,
                source_turn_id="turn_bad_1",
                summary="bad persona proposal",
                target="persona",
                payload={"value": "modify persona"},
                confidence=0.99,
            ),
            StateProposal.create(
                ProposalType.TASK_STATE_UPDATE,
                source_turn_id="turn_bad_2",
                summary="bad relationship proposal",
                target="relationship",
                payload={"value": "modify relationship"},
                confidence=0.99,
            ),
        ]
        result = ProposalValidator().validate(proposals)

        self.assertEqual(len(result.accepted), 0)
        self.assertEqual(len(result.rejected), 2)
        self.assertEqual({d.reason for d in result.decisions}, {"protected_field_runtime_authority_required"})

    def test_tc_361010_006_worker_crash_recovery_does_not_affect_main_loop_or_state(self):
        class CrashingJob(MaintenanceJob):
            def run(self, event: WorkerEvent):  # type: ignore[override]
                raise RuntimeError("simulated worker crash")

        runtime = AsyncContextMaintenanceRuntime(job=CrashingJob())
        session = JuliaSessionState.create(session_id="conv", project="Julia Runtime")
        task = JuliaTaskState.create(task_id="task", objective="Main conversation loop", session_id="conv")
        manager = JuliaStateManager()

        runtime.enqueue(WorkerEvent.turn_completed(source_turn_id="turn_crash", payload={"user": "trigger"}))
        result = runtime.run_once()
        transition = manager.apply_mutations(session_state=session, task_state=task, mutations=[], persist=False)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.proposals), 0)
        self.assertEqual(transition.next_session, session)
        self.assertEqual(transition.next_task, task)


if __name__ == "__main__":
    unittest.main()
