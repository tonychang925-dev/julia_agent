from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.context_os.memory_router import MemoryScopeClassifier, MemoryScopePolicy
from runtime.context_os.provenance import ContextSourceType, ProvenanceBuilder
from runtime.evidence import SemanticContextRetriever
from runtime.evidence.evidence_chunk import EvidenceChunk
from runtime.evidence.semantic_ranker import RankedEvidence
from runtime.memory.governance import MemoryGovernanceManager
from runtime.memory.memory_object import MemoryObject


def memory(memory_id, memory_type, summary, topics, importance=None):
    return MemoryObject(
        id=memory_id,
        type=memory_type,
        summary=summary,
        content={},
        topics=topics,
        importance=importance or {"emotional": 0.3, "relationship": 0.3, "technical": 0.8, "recurrence": 0.6},
        timestamp="2026-07-29T00:00:00Z",
        source="test",
    )


def provenance(memory_id, *, source_type=ContextSourceType.GOVERNED_MEMORY.value, authority=0.95):
    return ProvenanceBuilder().runtime_inference(
        block_id=f"memory:{memory_id}",
        source_id=f"memory:{memory_id}",
        reason="test provenance",
        confidence=0.8,
        injected_by="semantic_evidence_projection",
        cognitive_scope="engineering",
    ).__class__.create(
        context_block_id=f"memory:{memory_id}",
        source_type=source_type,
        source_id=f"memory:{memory_id}",
        speaker="memory",
        authority=authority,
        confidence=0.8,
        retrieval_reason=("semantic_match",),
        injection_reason="governed_memory_retrieval",
        injected_by="semantic_evidence_projection",
        current_task_relevance=0.7,
        cognitive_scope="engineering",
    )


class Phase3752MemoryRouterTests(unittest.TestCase):
    def test_tc_3752_001_engineering_isolation(self):
        scope = MemoryScopeClassifier().classify(user_input="继续设计 Context OS Memory Router", cognitive_mode="engineering_collaboration")
        policy = MemoryScopePolicy()
        technical = policy.decide(
            memory_id="project_context_os",
            memory_class="project_milestone",
            scope=scope,
            provenance=provenance("project_context_os"),
            semantic_score=0.7,
        )
        relationship = policy.decide(
            memory_id="relationship_foundation",
            memory_class="relationship_foundation",
            scope=scope,
            provenance=provenance("relationship_foundation"),
            semantic_score=0.9,
        )

        self.assertEqual(scope.scope, "engineering")
        self.assertEqual(technical.action, "inject")
        self.assertEqual(relationship.action, "suppress")
        self.assertEqual(relationship.reason, "cognitive_scope_mismatch")

    def test_tc_3752_002_emotional_scope(self):
        scope = MemoryScopeClassifier().classify(user_input="今天有点累，想让 Julia 陪我一下", cognitive_mode="emotional_support")
        policy = MemoryScopePolicy()
        relationship = policy.decide(
            memory_id="tony_julia_relationship",
            memory_class="relationship_foundation",
            scope=scope,
            provenance=provenance("tony_julia_relationship"),
            semantic_score=0.7,
        )

        self.assertEqual(scope.scope, "emotional")
        self.assertIn("relationship", scope.allowed_memory)
        self.assertEqual(relationship.action, "inject")

    def test_tc_3752_003_same_memory_different_scope(self):
        policy = MemoryScopePolicy()
        engineering = MemoryScopeClassifier().classify(user_input="设计 Julia Runtime 架构", cognitive_mode="engineering_collaboration")
        emotional = MemoryScopeClassifier().classify(user_input="你还记得我们为什么做 Julia 吗", cognitive_mode="emotional_support")
        prov = provenance("julia_runtime_origin_relationship")

        engineering_decision = policy.decide(
            memory_id="julia_runtime_origin_relationship",
            memory_class="relationship_foundation",
            scope=engineering,
            provenance=prov,
            semantic_score=0.85,
        )
        emotional_decision = policy.decide(
            memory_id="julia_runtime_origin_relationship",
            memory_class="relationship_foundation",
            scope=emotional,
            provenance=prov,
            semantic_score=0.85,
        )

        self.assertEqual(engineering_decision.action, "suppress")
        self.assertEqual(emotional_decision.action, "inject")

    def test_tc_3752_004_provenance_enforcement(self):
        scope = MemoryScopeClassifier().classify(user_input="继续设计 Context OS", cognitive_mode="engineering_collaboration")
        decision = MemoryScopePolicy().decide(
            memory_id="memory_without_provenance",
            memory_class="project_milestone",
            scope=scope,
            provenance=None,
            semantic_score=0.99,
        )

        self.assertEqual(decision.action, "suppress")
        self.assertEqual(decision.reason, "missing_provenance")
        self.assertTrue(decision.provenance_required)

    def test_tc_3752_005_retrieval_is_not_injection(self):
        scope = MemoryScopeClassifier().classify(user_input="Phase 3.7.5 设计 Memory Router", cognitive_mode="engineering_collaboration")
        decision = MemoryScopePolicy().decide(
            memory_id="memory_semantic_intimacy_mode_l1_l4_boundary_definition",
            memory_class="relationship_foundation",
            scope=scope,
            provenance=provenance("memory_semantic_intimacy_mode_l1_l4_boundary_definition"),
            semantic_score=0.99,
        )

        self.assertEqual(decision.action, "suppress")
        self.assertIn(decision.reason, {"cognitive_scope_mismatch", "high_retrieval_score_but_blocked_by_scope"})

    def test_tc_3752_006_semantic_retriever_emits_route_and_exclusion_metadata(self):
        _section, meta = SemanticContextRetriever(ROOT).prompt_section("Phase 3.7.5 Memory Router engineering context", limit=8, cognitive_mode="engineering_collaboration")

        self.assertIn("scope_decision", meta)
        self.assertIn("route_decisions", meta)
        self.assertIn("provenance_chain", meta)
        excluded = [record for record in meta["provenance_chain"]["records"] if record["decision"] == "excluded"]
        self.assertTrue(meta["provenance_validation"]["valid"])
        self.assertTrue(isinstance(excluded, list))

    def test_tc_3752_007_suppressed_memory_not_rendered_into_prompt(self):
        retriever = SemanticContextRetriever(ROOT)
        technical_chunk = EvidenceChunk(
            id="memory_project_router",
            source_type="memory",
            content="Project milestone: Memory Router controls technical context injection.",
            speaker="memory",
            authority=0.95,
            topics=["Memory Router", "technical"],
            provenance={"memory_type": "semantic", "importance": 0.9},
        )
        relationship_chunk = EvidenceChunk(
            id="memory_relationship_private_anchor",
            source_type="memory",
            content="PRIVATE_RELATIONSHIP_ANCHOR_SHOULD_NOT_RENDER",
            speaker="memory",
            authority=0.95,
            topics=["relationship"],
            provenance={"memory_type": "relationship", "importance": 1.0},
        )
        retriever.retrieve = lambda query, limit=8: [
            RankedEvidence(technical_chunk, 0.7, 0.95, 0.9, 0.0, 0.8, ["semantic_match"]),
            RankedEvidence(relationship_chunk, 0.99, 0.95, 1.0, 0.0, 0.95, ["semantic_match"]),
        ]

        section, meta = retriever.prompt_section("继续设计 Context OS Memory Router", cognitive_mode="engineering_collaboration")

        self.assertIn("Memory Router controls technical context injection", section)
        self.assertNotIn("PRIVATE_RELATIONSHIP_ANCHOR_SHOULD_NOT_RENDER", section)
        rendered_ids = {item["id"] for item in meta["sources"]}
        self.assertIn("memory_project_router", rendered_ids)
        self.assertNotIn("memory_relationship_private_anchor", rendered_ids)
        suppressed = [item for item in meta["route_decisions"] if item["memory_id"] == "memory_relationship_private_anchor"]
        self.assertEqual(suppressed[0]["action"], "suppress")


if __name__ == "__main__":
    unittest.main()
