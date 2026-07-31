from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.memory import MemoryObject, MemoryRuntime
from runtime.memory.governance import MemoryGovernanceDecision, MemoryGovernanceManager


def memory(mid: str, *, mtype="episodic", summary="", topics=None, importance=None, content=None) -> MemoryObject:
    return MemoryObject(
        id=mid,
        type=mtype,
        summary=summary or mid,
        content=content or {},
        topics=topics or [],
        importance=importance or {"emotional": 0.5, "relationship": 0.5, "technical": 0.5, "recurrence": 0.5},
        timestamp="2026-07-27T00:00:00Z",
        source="test",
    )


class Phase36MemoryGovernanceTests(unittest.TestCase):
    def test_tc_phase364_001_core_identity_protection(self):
        # TC-PHASE364-001
        item = memory(
            "m_core",
            mtype="relationship",
            summary="Julia exists to preserve identity continuity and independent existence across models.",
            topics=["identity continuity", "core identity"],
            importance={"emotional": 0.95, "relationship": 1.0, "technical": 0.7, "recurrence": 0.95},
        )

        decision = MemoryGovernanceManager().decide(item)

        self.assertEqual(decision.memory_class, "core_identity")
        self.assertEqual(decision.protection_level, "immutable_permanent")
        self.assertIn("identity_context", decision.allowed_effects)
        self.assertEqual(decision.retention_policy, "permanent_no_decay_archive")

    def test_tc_phase364_002_project_milestone_classification(self):
        # TC-PHASE364-002
        item = memory(
            "m_milestone",
            summary="Tony completed DirectLLMBridge and ContextCompiler for Julia Runtime Phase 3.",
            topics=["Julia Runtime", "DirectLLMBridge", "ContextCompiler"],
            importance={"emotional": 0.7, "relationship": 0.6, "technical": 0.95, "recurrence": 0.85},
        )

        decision = MemoryGovernanceManager().decide(item)

        self.assertEqual(decision.memory_class, "project_milestone")
        self.assertIn("technical_memory", decision.allowed_effects)
        self.assertNotIn("identity_context", decision.allowed_effects)

    def test_tc_phase364_003_behavior_preference_classification(self):
        # TC-PHASE364-003
        item = memory(
            "m_pref",
            mtype="relationship",
            summary="Tony 喜欢先看架构设计，再看代码实现。",
            topics=["interaction preference"],
            importance={"emotional": 0.4, "relationship": 0.75, "technical": 0.5, "recurrence": 0.8},
        )

        decision = MemoryGovernanceManager().decide(item)

        self.assertEqual(decision.memory_class, "behavior_preference")
        self.assertEqual(decision.allowed_effects, ["response_style", "memory_retrieval"])
        self.assertNotIn("relationship_context", decision.allowed_effects)

    def test_tc_phase364_004_temp_event_classification(self):
        # TC-PHASE364-004
        item = memory(
            "m_temp",
            summary="pytest failed once during a temporary debug run.",
            topics=["temporary", "debug log"],
            importance={"emotional": 0.05, "relationship": 0.05, "technical": 0.2, "recurrence": 0.0},
        )

        decision = MemoryGovernanceManager().decide(item)

        self.assertEqual(decision.memory_class, "temp_event")
        self.assertEqual(decision.allowed_effects, ["archive"])
        self.assertEqual(decision.retention_policy, "fast_archive")

    def test_tc_phase364_005_allowed_effects_are_scoped_by_class(self):
        # TC-PHASE364-005
        milestone = memory(
            "m_project",
            summary="Completed Memory Runtime milestone for Julia Runtime.",
            topics=["Julia Runtime", "Memory Runtime"],
            importance={"emotional": 0.6, "relationship": 0.5, "technical": 0.9, "recurrence": 0.8},
        )
        normal = memory(
            "m_episode",
            summary="Tony discussed one ordinary technical question.",
            topics=["ordinary"],
            importance={"emotional": 0.2, "relationship": 0.2, "technical": 0.4, "recurrence": 0.2},
        )

        milestone_decision = MemoryGovernanceManager().decide(milestone)
        normal_decision = MemoryGovernanceManager().decide(normal)

        self.assertIn("project_continuity", milestone_decision.allowed_effects)
        self.assertNotIn("identity_context", milestone_decision.allowed_effects)
        self.assertEqual(normal_decision.allowed_effects, ["memory_retrieval"])

    def test_tc_phase364_006_governance_explainability(self):
        # TC-PHASE364-006
        decision = MemoryGovernanceManager().decide(memory("m", summary="ordinary note"))

        self.assertIsInstance(decision, MemoryGovernanceDecision)
        self.assertTrue(decision.reason)
        self.assertGreaterEqual(decision.confidence, 0.0)
        self.assertIn(decision.memory_class, {
            "core_identity", "relationship_foundation", "project_milestone", "behavior_preference", "normal_episode", "temp_event", "archival"
        })

    def test_tc_phase364_007_memory_runtime_governance_facade(self):
        # TC-PHASE364-007
        runtime = MemoryRuntime(ROOT)
        item = memory("m_core", mtype="relationship", summary="Julia exists for identity continuity.", topics=["identity continuity"], importance={"emotional": 0.9, "relationship": 0.95, "technical": 0.5, "recurrence": 0.9})

        decision = runtime.govern_memory(item)

        self.assertEqual(decision.memory_id, "m_core")
        self.assertEqual(decision.memory_class, "core_identity")


if __name__ == "__main__":
    unittest.main()
