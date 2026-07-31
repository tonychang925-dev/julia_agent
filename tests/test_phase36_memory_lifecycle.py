from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.memory import MemoryObject
from runtime.memory.lifecycle import MemoryLifecycleDecision, MemoryLifecycleManager


def memory(mid: str, *, mtype="episodic", summary="", topics=None, importance=None) -> MemoryObject:
    return MemoryObject(
        id=mid,
        type=mtype,
        summary=summary or mid,
        content={},
        topics=topics or [],
        importance=importance or {"emotional": 0.5, "relationship": 0.5, "technical": 0.5, "recurrence": 0.5},
        timestamp="2026-07-27T00:00:00Z",
        source="test",
    )


class Phase36MemoryLifecycleTests(unittest.TestCase):
    def test_tc_phase363_001_reinforcement_increases_recurrence_and_importance(self):
        # TC-PHASE363-001
        item = memory(
            "m_runtime",
            summary="Tony worked on Julia Runtime migration.",
            topics=["Julia Runtime", "Model Migration"],
            importance={"emotional": 0.4, "relationship": 0.6, "technical": 0.7, "recurrence": 0.4},
        )

        result = MemoryLifecycleManager().apply([item], referenced_topics=["Julia Runtime"])
        updated = result.memories[0]

        self.assertEqual(result.decisions[0].action, "reinforce")
        self.assertGreater(updated.importance["recurrence"], item.importance["recurrence"])
        self.assertGreater(updated.importance["technical"], item.importance["technical"])

    def test_tc_phase363_002_decay_low_value_memory(self):
        # TC-PHASE363-002
        item = memory(
            "m_temp",
            summary="One-off minor note with low future value.",
            topics=["minor note"],
            importance={"emotional": 0.1, "relationship": 0.1, "technical": 0.2, "recurrence": 0.05},
        )

        result = MemoryLifecycleManager().apply([item])
        updated = result.memories[0]

        self.assertEqual(result.decisions[0].action, "decay")
        self.assertLess(updated.importance["technical"], item.importance["technical"])

    def test_tc_phase363_003_merge_related_milestones(self):
        # TC-PHASE363-003
        items = [
            memory("m_direct", summary="Tony completed DirectLLMBridge.", topics=["Julia Runtime", "DirectLLMBridge"], importance={"emotional": 0.7, "relationship": 0.6, "technical": 0.9, "recurrence": 0.8}),
            memory("m_context", summary="Tony completed ContextCompiler.", topics=["Julia Runtime", "ContextCompiler"], importance={"emotional": 0.7, "relationship": 0.6, "technical": 0.9, "recurrence": 0.8}),
            memory("m_cognitive", summary="Tony completed Cognitive Runtime.", topics=["Julia Runtime", "Cognitive Runtime"], importance={"emotional": 0.8, "relationship": 0.8, "technical": 0.95, "recurrence": 0.85}),
        ]

        result = MemoryLifecycleManager().apply(items)

        self.assertTrue(all(decision.action == "merge" for decision in result.decisions))
        self.assertEqual(len(result.memories), 1)
        self.assertIn("Julia Runtime Independence", result.memories[0].summary)
        self.assertEqual(set(result.memories[0].content["merged_memory_ids"]), {"m_direct", "m_context", "m_cognitive"})

    def test_tc_phase363_004_archive_obsolete_low_value_memory(self):
        # TC-PHASE363-004
        item = memory(
            "m_obsolete",
            summary="obsolete temporary failed test debug log",
            topics=["debug log"],
            importance={"emotional": 0.05, "relationship": 0.05, "technical": 0.15, "recurrence": 0.0},
        )

        result = MemoryLifecycleManager().apply([item])

        self.assertEqual(result.decisions[0].action, "archive")
        self.assertTrue(result.memories[0].content["archived"])

    def test_tc_phase363_005_relationship_core_memory_protected(self):
        # TC-PHASE363-005
        item = memory(
            "m_core_relationship",
            mtype="relationship",
            summary="Tony created Julia to preserve identity continuity and independent existence.",
            topics=["identity continuity", "created Julia"],
            importance={"emotional": 0.95, "relationship": 1.0, "technical": 0.5, "recurrence": 0.95},
        )

        result = MemoryLifecycleManager().apply([item])

        self.assertEqual(result.decisions[0].action, "retain")
        self.assertEqual(result.decisions[0].reason, "protected_core_relationship_memory")
        self.assertEqual(result.memories[0], item)

    def test_tc_phase363_006_lifecycle_decision_explainability(self):
        # TC-PHASE363-006
        decision = MemoryLifecycleManager().evaluate([
            memory("m", summary="Tony worked on Julia Runtime migration.", topics=["Julia Runtime"], importance={"emotional": 0.4, "relationship": 0.6, "technical": 0.7, "recurrence": 0.4})
        ], referenced_topics=["Julia Runtime"])[0]

        self.assertIsInstance(decision, MemoryLifecycleDecision)
        self.assertIn(decision.action, {"reinforce", "merge", "decay", "archive", "retain"})
        self.assertTrue(decision.reason)
        self.assertGreaterEqual(decision.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
