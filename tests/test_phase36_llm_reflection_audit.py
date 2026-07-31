from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_state import ConversationTurn
from runtime.memory import MemoryObject
from runtime.memory.governance import MemoryGovernanceManager
from runtime.memory.governance.audit import GovernanceAuditLogger, GovernanceAuditQuery, GovernanceEvent
from runtime.reflection import MemoryCandidate, ReflectionEngine, ReflectionInput
from runtime.reflection.llm import CandidateValidator, FakeLLMReflector, LLMReflectionResult
from runtime.situation import SituationContext


def situation() -> SituationContext:
    return SituationContext(
        current_activity="testing LLM-assisted Reflection",
        environment="software_architecture",
        goal="governed reflection",
        interaction_mode="engineering_collaboration",
        active_topics=["Julia Runtime", "Reflection"],
    )


def reflection_input(text: str) -> ReflectionInput:
    return ReflectionInput(
        conversation_arc="technical_progress",
        recent_turns=[ConversationTurn(1, text, "这是重要里程碑。", "2026-07-27", ["Julia Runtime"], "engineering_collaboration")],
        active_topics=["Julia Runtime", "Host Independence"],
        open_loops=[],
        situation_context=situation(),
    )


class Phase36LLMReflectionAuditTests(unittest.TestCase):
    def test_tc_phase365_001_llm_result_produces_candidate_only(self):
        # TC-PHASE365-001
        result = FakeLLMReflector().reflect(reflection_input("Tony completed DirectLLMBridge; Julia achieved host independence."))

        self.assertIsInstance(result, LLMReflectionResult)
        self.assertTrue(result.memory_candidates)
        self.assertTrue(all(isinstance(item, MemoryCandidate) for item in result.memory_candidates))
        self.assertFalse(any(isinstance(item, MemoryObject) for item in result.memory_candidates))

    def test_tc_phase365_002_candidate_validator_rejects_runtime_leakage(self):
        # TC-PHASE365-002
        leaked = MemoryCandidate(
            memory_type="semantic",
            summary="Julia uses deepseek backend latency optimization.",
            reason="runtime metadata should not become memory",
            importance={"technical": 0.9, "relationship": 0.1, "recurrence": 0.2, "emotional": 0.1},
            confidence=0.9,
            topics=["provider", "backend"],
            source="llm_reflection_fake",
        )

        result = CandidateValidator().validate(leaked)

        self.assertFalse(result.accepted)
        self.assertIn("runtime metadata", result.reason)

    def test_tc_phase365_003_governance_audit_event_written(self):
        # TC-PHASE365-003
        memory = MemoryObject(
            id="mem_project",
            type="episodic",
            summary="Tony completed DirectLLMBridge for Julia Runtime.",
            content={},
            topics=["Julia Runtime", "DirectLLMBridge"],
            importance={"technical": 0.95, "relationship": 0.7, "recurrence": 0.85, "emotional": 0.7},
            timestamp="2026-07-27",
            source="test",
        )
        decision = MemoryGovernanceManager().decide(memory)
        with tempfile.TemporaryDirectory() as tmp:
            event = GovernanceAuditLogger(tmp).log_decision(decision, timestamp="2026-07-27T00:00:00Z")
            events = GovernanceAuditQuery(tmp).find_by_memory_id("mem_project")

        self.assertIsInstance(event, GovernanceEvent)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].memory_class, decision.memory_class)
        self.assertEqual(events[0].allowed_effects, decision.allowed_effects)

    def test_tc_phase365_004_llm_cannot_override_governance(self):
        # TC-PHASE365-004
        # Simulate an LLM-proposed candidate claiming high significance in prose,
        # but the actual memory content is only a temporary debug experiment.
        memory = MemoryObject(
            id="mem_temp_claim",
            type="semantic",
            summary="temporary pytest failed once during debug; LLM claims CORE_IDENTITY",
            content={"llm_claimed_class": "CORE_IDENTITY"},
            topics=["temporary", "debug log"],
            importance={"technical": 0.2, "relationship": 0.1, "recurrence": 0.0, "emotional": 0.05},
            timestamp="2026-07-27",
            source="llm_reflection_fake",
        )

        decision = MemoryGovernanceManager().decide(memory)

        self.assertEqual(decision.memory_class, "temp_event")
        self.assertEqual(decision.allowed_effects, ["archive"])
        self.assertNotIn("identity_context", decision.allowed_effects)

    def test_tc_phase365_005_offline_fake_llm_reflection_pipeline(self):
        # TC-PHASE365-005
        candidates = ReflectionEngine().reflect_with_llm(
            reflection_input("Tony completed DirectLLMBridge and Julia achieved host independence."),
            FakeLLMReflector(),
        )

        self.assertEqual(len(candidates), 1)
        self.assertIn("host independence", candidates[0].summary.lower())
        self.assertGreaterEqual(candidates[0].confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
