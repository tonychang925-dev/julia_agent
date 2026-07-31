from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.memory import MemoryRuntime
from runtime.memory.persistence import MemoryPersistenceAdapter, MemoryPersistenceRequest
from runtime.reflection import MemoryCandidate


def candidate(**overrides) -> MemoryCandidate:
    values = {
        "memory_type": "episodic",
        "summary": "Tony completed Julia Runtime migration milestone.",
        "reason": "Major milestone for Julia identity continuity.",
        "importance": {"technical": 0.95, "relationship": 0.8, "recurrence": 0.9, "emotional": 0.85},
        "confidence": 0.92,
        "topics": ["Julia Runtime", "Model Migration"],
        "source": "reflection_runtime",
    }
    values.update(overrides)
    return MemoryCandidate(**values)


def request(item: MemoryCandidate) -> MemoryPersistenceRequest:
    return MemoryPersistenceRequest(candidate=item, source_reflection_id="reflection_001", created_at="2026-07-27T00:00:00Z")


class Phase36MemoryPersistenceTests(unittest.TestCase):
    def test_tc_phase361_001_candidate_accepted_creates_memory_object(self):
        # TC-PHASE361-001
        with tempfile.TemporaryDirectory() as tmp:
            result = MemoryPersistenceAdapter(tmp).persist(request(candidate()))
            path = Path(tmp) / "memory" / "episodic_memory.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertTrue(result.stored)
        self.assertEqual(result.action, "create")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "episodic")
        self.assertIn("source_reflection_id", rows[0]["content"])

    def test_tc_phase361_002_low_confidence_candidate_rejected(self):
        # TC-PHASE361-002
        with tempfile.TemporaryDirectory() as tmp:
            result = MemoryPersistenceAdapter(tmp).persist(request(candidate(confidence=0.3)))
            memory_dir = Path(tmp) / "memory"

        self.assertFalse(result.stored)
        self.assertEqual(result.action, "reject")
        self.assertFalse((memory_dir / "episodic_memory.jsonl").exists())

    def test_tc_phase361_003_duplicate_candidate_merges_existing_memory(self):
        # TC-PHASE361-003
        with tempfile.TemporaryDirectory() as tmp:
            adapter = MemoryPersistenceAdapter(tmp)
            first = adapter.persist(request(candidate(summary="Tony started Julia Runtime migration.")))
            second = adapter.persist(request(candidate(summary="Tony completed Julia Runtime migration journey.")))
            path = Path(tmp) / "memory" / "episodic_memory.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(first.action, "create")
        self.assertEqual(second.action, "merge")
        self.assertEqual(len(rows), 1)
        self.assertIn("completed", rows[0]["summary"])
        self.assertIn("merged_with", rows[0]["content"])

    def test_tc_phase361_004_memory_type_preserved_for_relationship_candidate(self):
        # TC-PHASE361-004
        item = candidate(
            memory_type="relationship",
            summary="Tony values Julia identity continuity across models.",
            importance={"technical": 0.65, "relationship": 0.95, "recurrence": 0.9, "emotional": 0.8},
            topics=["identity continuity"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = MemoryPersistenceAdapter(tmp).persist(request(item))
            path = Path(tmp) / "memory" / "relationship_memory.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertTrue(result.stored)
        self.assertEqual(rows[0]["type"], "relationship")
        self.assertGreaterEqual(rows[0]["importance"]["relationship"], 0.95)

    def test_tc_phase361_005_runtime_leakage_rejected(self):
        # TC-PHASE361-005
        item = candidate(summary="provider deepseek latency metadata should not persist")
        with tempfile.TemporaryDirectory() as tmp:
            result = MemoryPersistenceAdapter(tmp).persist(request(item))

        self.assertFalse(result.stored)
        self.assertEqual(result.action, "reject")
        self.assertIn("runtime metadata", result.reason)

    def test_tc_phase361_006_memory_runtime_facade_persists_candidate(self):
        # TC-PHASE361-006
        with tempfile.TemporaryDirectory() as tmp:
            runtime = MemoryRuntime(tmp)
            result = runtime.persist_candidate(request(candidate()))
            recalled = runtime.retrieve("Julia Runtime migration", limit=3)

        self.assertTrue(result.stored)
        self.assertTrue(any("Julia Runtime" in memory.summary for memory in recalled))


if __name__ == "__main__":
    unittest.main()
