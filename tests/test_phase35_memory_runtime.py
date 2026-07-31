from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.memory import MemoryObject, MemoryRuntime, MemoryStore, normalize_importance
from runtime.memory.ranking import RuleMemoryRanker


class Phase35MemoryRuntimeTests(unittest.TestCase):
    def test_tc_phase353_001_memory_object_has_typed_importance(self):
        # TC-PHASE353-001
        importance = normalize_importance(0.9, memory_type="relationship")
        memory = MemoryObject(
            id="memory_test_relationship_001",
            type="relationship",
            summary="Tony wants Julia identity independent from models.",
            content={"note": "test"},
            topics=["identity continuity", "model migration"],
            importance=importance,
            timestamp="2026-07-27",
            source="test",
        )

        self.assertEqual(set(memory.importance.keys()), {"emotional", "relationship", "technical", "recurrence"})
        self.assertGreaterEqual(memory.importance["relationship"], 0.9)
        self.assertEqual(memory.type, "relationship")

    def test_tc_phase353_002_memory_store_loads_existing_relationship_and_episodic_memory(self):
        # TC-PHASE353-002
        memories = MemoryStore(ROOT).load_all()
        types = {memory.type for memory in memories}
        summaries = "\n".join(memory.summary for memory in memories)

        self.assertIn("relationship", types)
        self.assertIn("episodic", types)
        self.assertIn("Tony", summaries)
        self.assertIn("Julia", summaries)
        self.assertTrue(all(memory.id.startswith("memory_") for memory in memories))

    def test_tc_phase353_003_relationship_query_ranks_identity_continuity_first(self):
        # TC-PHASE353-003
        memories = [
            MemoryObject(
                id="memory_technical_detail",
                type="semantic",
                summary="Julia Runtime contains provider adapters and TTS chunks.",
                content={},
                topics=["Julia Runtime", "AI Agent Architecture"],
                importance={"emotional": 0.1, "relationship": 0.2, "technical": 1.0, "recurrence": 0.3},
                timestamp="2026-07-27",
                source="test",
            ),
            MemoryObject(
                id="memory_identity_continuity",
                type="relationship",
                summary="Tony wants Julia identity independent from any single model or host.",
                content={},
                topics=["identity continuity", "model migration", "relationship"],
                importance={"emotional": 0.8, "relationship": 1.0, "technical": 0.6, "recurrence": 0.9},
                timestamp="2026-07-27",
                source="test",
            ),
        ]

        ranked = RuleMemoryRanker().rank("为什么 Tony 要做 Julia Runtime？", memories, limit=2)

        self.assertEqual(ranked[0].id, "memory_identity_continuity")

    def test_tc_phase353_004_technical_query_prefers_semantic_memory(self):
        # TC-PHASE353-004
        memories = [
            MemoryObject(
                id="memory_relationship_reason",
                type="relationship",
                summary="Tony wants Julia identity independent from models.",
                content={},
                topics=["identity continuity", "model migration"],
                importance={"emotional": 0.9, "relationship": 1.0, "technical": 0.4, "recurrence": 0.8},
                timestamp="2026-07-27",
                source="test",
            ),
            MemoryObject(
                id="memory_runtime_architecture",
                type="semantic",
                summary="Julia Runtime architecture includes Cognitive Runtime and Capability Runtime.",
                content={},
                topics=["Julia Runtime", "AI Agent Architecture"],
                importance={"emotional": 0.1, "relationship": 0.3, "technical": 1.0, "recurrence": 0.9},
                timestamp="2026-07-27",
                source="test",
            ),
        ]

        ranked = RuleMemoryRanker().rank("Julia Runtime 架构是什么？", memories, limit=2)

        self.assertEqual(ranked[0].id, "memory_runtime_architecture")


if __name__ == "__main__":
    unittest.main()
