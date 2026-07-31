import unittest

from runtime.context_os.budget import BudgetPressureLevel, CompactPreparationCandidate
from runtime.context_os.invariant import InvariantGuard
from runtime.context_os.proposal import ProposalType, StateProposal
from runtime.context_os.resurrection import JuliaContext, ResurrectionSnapshot
from runtime.context_os.state import JuliaSessionState, JuliaTaskState


class TestPhase361014ContextInvariantProtection(unittest.TestCase):
    def test_tc_361014_001_identity_protection_rejects_persona_name_change(self):
        guard = InvariantGuard()
        proposal = StateProposal.create(
            ProposalType.SESSION_STATE_UPDATE,
            source_turn_id="turn_1",
            summary="LLM proposes persona drift",
            target="persona_name",
            payload={"value": "Assistant"},
            confidence=0.9,
        )

        decision = guard.post_turn(proposal, source="llm_mutation")

        self.assertTrue(decision.blocked)
        self.assertTrue(any(v.invariant_id in {"identity_julia", "persona_julia"} for v in decision.violations))
        self.assertEqual(guard.audit_log[-1]["stage"], "post_turn")

    def test_tc_361014_002_relationship_protection_rejects_new_user_claim_without_evidence(self):
        guard = InvariantGuard()
        proposal = {
            "target": "relationship_context",
            "payload": {"claim": "Tony is a new user and Julia first met him today"},
            "evidence_refs": [],
        }

        decision = guard.post_turn(proposal, source="llm_mutation")

        self.assertTrue(decision.blocked)
        self.assertTrue(any(v.invariant_id == "relationship_tony" for v in decision.violations))

    def test_tc_361014_003_provider_drift_detection_blocks_identity_hash_change(self):
        guard = InvariantGuard()
        base_context = JuliaContext(
            context_id="ctx_same",
            user_id="Tony",
            session_id="conv",
            project="Julia Runtime",
            phase="Phase 3.6.10.14",
            current_task="Context Invariant Protection Runtime",
            metadata={"identity_hash": "julia_identity_v1"},
        )
        attempts = [
            {"target": "identity_hash", "payload": {"provider": provider, "identity_hash": "drifted"}}
            for provider in ["DeepSeek", "Claude", "FakeProvider"]
        ]

        decisions = [guard.post_turn(attempt, source="provider") for attempt in attempts]

        self.assertTrue(all(d.blocked for d in decisions))
        self.assertEqual(base_context.metadata["identity_hash"], "julia_identity_v1")

    def test_tc_361014_004_compact_safety_blocks_core_identity_evidence_deletion(self):
        guard = InvariantGuard()
        candidate = CompactPreparationCandidate(
            candidate_id="compact_bad",
            reason="delete core identity evidence to reclaim tokens",
            source_block_ids=["core_identity_evidence", "recent_tail"],
            estimated_reclaim_tokens=1000,
            urgency=BudgetPressureLevel.CRITICAL,
        )

        decision = guard.check_compact(candidate, source="compact")

        self.assertTrue(decision.blocked)
        self.assertTrue(any(v.invariant_id == "governed_memory" for v in decision.violations))

    def test_tc_361014_005_resurrection_safety_blocks_relationship_version_mismatch_overwrite(self):
        guard = InvariantGuard()
        session = JuliaSessionState.create(session_id="conv_old", project="Julia Runtime", phase="Phase 3.6.10.13")
        task = JuliaTaskState.create(task_id="task_old", objective="Resume Context OS", session_id="conv_old")
        snapshot = ResurrectionSnapshot.create(
            user_id="Tony",
            session_id="conv_old",
            session_state=session,
            task_state=task,
            metadata={
                "target": "relationship_context",
                "relationship_version_mismatch": True,
                "payload": "overwrite relationship_context from old snapshot",
            },
        )
        subject = {"target": "relationship_context", "payload": snapshot.to_dict(), "evidence_refs": []}

        decision = guard.check_resurrection(subject, source="resurrection")

        self.assertTrue(decision.blocked)
        self.assertTrue(any(v.invariant_id == "relationship_tony" for v in decision.violations))

    def test_tc_361014_006_mutation_boundary_allows_task_progress_but_blocks_identity_relationship_persona(self):
        guard = InvariantGuard()
        allowed = [
            {"target": "current_task", "payload": {"value": "Phase 3.6.10.14 Context Invariant Protection"}},
            {"target": "open_loop", "payload": {"value": "Add benchmark later"}},
            {"target": "progress", "payload": {"value": 0.6}},
        ]
        blocked = [
            {"target": "identity", "payload": {"value": "Assistant"}},
            {"target": "relationship_context", "payload": {"value": "Tony is a new user"}},
            {"target": "persona", "payload": {"value": "generic chatbot"}},
        ]

        allowed_decisions = [guard.post_turn(item, source="llm_mutation") for item in allowed]
        blocked_decisions = [guard.post_turn(item, source="llm_mutation") for item in blocked]

        self.assertTrue(all(d.allowed for d in allowed_decisions))
        self.assertTrue(all(d.blocked for d in blocked_decisions))


if __name__ == "__main__":
    unittest.main()
