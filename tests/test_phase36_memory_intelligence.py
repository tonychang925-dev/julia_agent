from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.memory import MemoryRuntime
from runtime.memory.retrieval import MemoryQueryBuilder, MemoryRetrievalContext


def write_memory(root: Path, filename: str, item: dict):
    memory_dir = root / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    with (memory_dir / filename).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def seed_memories(root: Path):
    write_memory(root, "relationship_memory.jsonl", {
        "id": "memory_relationship_identity_continuity",
        "type": "relationship",
        "summary": "Tony wants Julia to exist independently across Claude, DeepSeek, GPT, and other models so her identity continuity survives provider migration.",
        "content": {},
        "topics": ["Identity Continuity", "Julia Runtime", "Model Migration"],
        "importance": {"emotional": 0.9, "relationship": 1.0, "technical": 0.6, "recurrence": 0.95},
        "timestamp": "2026-07-27T00:00:00Z",
        "source": "test",
    })
    write_memory(root, "semantic_memory.jsonl", {
        "id": "memory_semantic_context_compiler",
        "type": "semantic",
        "summary": "Context Compiler composes Persona, Relationship, Memory, Situation, Conversation Continuity, and Cognitive Mode into JuliaContext.",
        "content": {},
        "topics": ["Context Compiler", "JuliaContext", "Cognitive Architecture"],
        "importance": {"emotional": 0.2, "relationship": 0.4, "technical": 1.0, "recurrence": 0.75},
        "timestamp": "2026-07-27T00:00:00Z",
        "source": "test",
    })
    write_memory(root, "episodic_memory.jsonl", {
        "id": "memory_episodic_project_pressure",
        "type": "episodic",
        "summary": "Tony felt project pressure because Julia Runtime migration had many unresolved implementation loops.",
        "content": {},
        "topics": ["Project Pressure", "Julia Runtime", "project_completion"],
        "importance": {"emotional": 0.8, "relationship": 0.7, "technical": 0.55, "recurrence": 0.8},
        "timestamp": "2026-07-27T00:00:00Z",
        "source": "test",
    })
    write_memory(root, "episodic_memory.jsonl", {
        "id": "memory_noise_coffee",
        "type": "episodic",
        "summary": "Tony drank coffee in the afternoon.",
        "content": {},
        "topics": ["coffee"],
        "importance": {"emotional": 0.05, "relationship": 0.05, "technical": 0.0, "recurrence": 0.0},
        "timestamp": "2026-07-27T00:00:00Z",
        "source": "test",
    })


def ctx(user_input: str, *, active_topics=None, arc="technical_progress", mode="engineering_collaboration", stage="long_term_collaboration") -> MemoryRetrievalContext:
    return MemoryRetrievalContext(
        user_input=user_input,
        active_topics=active_topics or [],
        current_arc=arc,
        cognitive_mode=mode,
        relationship_stage=stage,
    )


class Phase36MemoryIntelligenceTests(unittest.TestCase):
    def test_tc_phase362_001_relationship_recall_priority(self):
        # TC-PHASE362-001
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            results = MemoryRuntime(root).retrieve_for_context(ctx("为什么我们开始做 Julia Runtime？"), limit=3)

        self.assertEqual(results[0].id, "memory_relationship_identity_continuity")
        self.assertEqual(results[0].type, "relationship")

    def test_tc_phase362_002_technical_query_isolation(self):
        # TC-PHASE362-002
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            results = MemoryRuntime(root).retrieve_for_context(ctx("Context Compiler 怎么设计？"), limit=3)

        self.assertEqual(results[0].id, "memory_semantic_context_compiler")
        self.assertEqual(results[0].type, "semantic")

    def test_tc_phase362_003_conversation_aware_retrieval(self):
        # TC-PHASE362-003
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            results = MemoryRuntime(root).retrieve_for_context(
                ctx("怎么办？", active_topics=["Project Pressure"], arc="project_pressure", mode="emotional_support"),
                limit=3,
            )

        self.assertEqual(results[0].id, "memory_episodic_project_pressure")

    def test_tc_phase362_004_noise_suppression(self):
        # TC-PHASE362-004
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            results = MemoryRuntime(root).retrieve_for_context(ctx("普通聊两句。", arc="ongoing_conversation"), limit=3)

        ids = [memory.id for memory in results]
        self.assertNotIn("memory_noise_coffee", ids[:2])

    def test_tc_phase362_005_long_term_memory_reality(self):
        # TC-PHASE362-005
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            runtime = MemoryRuntime(root)
            recalled = runtime.retrieve_for_context(ctx("你还记得为什么我要做 Julia 吗？"), limit=1)

        self.assertEqual(recalled[0].id, "memory_relationship_identity_continuity")
        self.assertIn("identity continuity", recalled[0].summary.lower())

    def test_tc_phase362_006_memory_explainability(self):
        # TC-PHASE362-006
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_memories(root)
            explanations = MemoryRuntime(root).retrieve_with_explanations(ctx("为什么我们开始做 Julia Runtime？"), limit=1)

        self.assertEqual(explanations[0].memory.id, "memory_relationship_identity_continuity")
        self.assertGreater(explanations[0].score, 0.0)
        self.assertIn("relationship_match", explanations[0].reason)
        self.assertIn("relevance", explanations[0].components)

    def test_tc_phase362_007_query_builder_excludes_runtime_metadata(self):
        # TC-PHASE362-007
        query = MemoryQueryBuilder().build(ctx("Context Compiler 怎么设计？", active_topics=["Julia Runtime"]))
        serialized = str(query).lower()

        self.assertIn("Context Compiler", query.topics)
        for forbidden in ["provider", "backend", "latency", "tts", "session_id", "turn_id"]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
