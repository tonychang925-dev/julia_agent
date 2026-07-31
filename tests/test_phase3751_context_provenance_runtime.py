from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.context_os.provenance import (
    ContextSourceType,
    ProvenanceBuilder,
    ProvenanceValidator,
)
from runtime.evidence import EvidenceChunk, RankedEvidence, SemanticContextRetriever


def chunk(**overrides):
    data = {
        "id": "archive:conv_xxx:1:tony",
        "source_type": "archive",
        "content": "Tony said E2E Alpha focuses on single-step governed E2E.",
        "session_id": "conv_xxx",
        "turn_id": 1,
        "timestamp": "2026-07-29T00:00:00Z",
        "speaker": "Tony",
        "authority": 0.9,
        "topics": ["E2E Integration Alpha"],
        "provenance": {"origin": "tony_input", "verified": True, "archive_role": "experience_archive"},
    }
    data.update(overrides)
    return EvidenceChunk(**data)


def ranked(evidence_chunk=None, **overrides):
    data = {
        "chunk": evidence_chunk or chunk(),
        "semantic_similarity": 0.72,
        "authority": (evidence_chunk or chunk()).authority,
        "memory_importance": 0.0,
        "recency": 0.7,
        "final_score": 0.81,
        "reason": ["semantic_match", "high_authority", "recency"],
    }
    data.update(overrides)
    return RankedEvidence(**data)


class Phase3751ContextProvenanceRuntimeTests(unittest.TestCase):
    def test_tc_3751_001_current_user_authority(self):
        record = ProvenanceBuilder().current_user(text="Tony current fact", cognitive_scope="engineering_collaboration")

        self.assertEqual(record.source_type, ContextSourceType.CURRENT_USER.value)
        self.assertEqual(record.speaker, "Tony")
        self.assertEqual(record.authority, 1.0)
        self.assertTrue(ProvenanceValidator().validate_record(record).valid)

    def test_tc_3751_002_archive_lineage(self):
        record = ProvenanceBuilder().from_ranked_evidence(ranked(), injected_by="conversation_continuity_projection")

        self.assertEqual(record.source_type, ContextSourceType.CONVERSATION_ARCHIVE.value)
        self.assertEqual(record.source_id, "archive:conv_xxx:1:tony")
        self.assertEqual(record.speaker, "Tony")
        self.assertEqual(record.injection_reason, "direct_previous_user_statement")

    def test_tc_3751_003_governed_memory_lineage(self):
        mem = chunk(
            id="memory:memory_project_julia_runtime",
            source_type="memory",
            speaker="memory",
            authority=0.95,
            provenance={"origin": "governed_memory", "verified": True, "memory_id": "memory_project_julia_runtime", "memory_type": "semantic"},
        )
        record = ProvenanceBuilder().from_ranked_evidence(ranked(mem))

        self.assertEqual(record.source_type, ContextSourceType.GOVERNED_MEMORY.value)
        self.assertEqual(record.source_id, "memory:memory_project_julia_runtime")
        self.assertEqual(record.source_version, "semantic")
        self.assertEqual(record.authority, 0.95)

    def test_tc_3751_004_provider_output_isolation(self):
        record = ProvenanceBuilder().runtime_inference(
            block_id="provider_summary",
            source_id="provider:turn:1",
            reason="provider_output_summary",
            confidence=0.6,
            injected_by="provider_projection",
        )
        # Deliberately create invalid provider-as-user fixture.
        invalid = record.__class__(**{**record.to_dict(), "source_type": ContextSourceType.PROVIDER_OUTPUT.value, "speaker": "Tony", "retrieval_reason": tuple(record.retrieval_reason), "excluded_domains": tuple(record.excluded_domains)})

        decision = ProvenanceValidator().validate_record(invalid)

        self.assertFalse(decision.valid)
        self.assertIn("provider_output_cannot_speak_as_tony", decision.errors)

    def test_tc_3751_005_runtime_inference_label(self):
        record = ProvenanceBuilder().runtime_inference(
            block_id="scope_inference",
            source_id="runtime:scope:e2e_alpha",
            reason="scope inferred from current task",
            confidence=0.82,
            injected_by="scope_classifier",
        )

        self.assertEqual(record.source_type, ContextSourceType.RUNTIME_INFERENCE.value)
        self.assertTrue(record.inferred)
        self.assertLessEqual(record.authority, 0.2)
        self.assertTrue(ProvenanceValidator().validate_record(record).valid)

    def test_tc_3751_006_exclusion_trace(self):
        record = ProvenanceBuilder().exclusion(
            source_id="memory_semantic_intimacy_mode_l1_l4_boundary_definition",
            source_type=ContextSourceType.GOVERNED_MEMORY.value,
            reason="cognitive_scope_mismatch",
            current_scope="engineering_collaboration",
            blocked_domains=("relationship", "intimacy"),
            authority=0.95,
            speaker="memory",
        )

        self.assertEqual(record.decision, "excluded")
        self.assertEqual(record.exclusion_reason, "cognitive_scope_mismatch")
        self.assertIn("intimacy", record.excluded_domains)

    def test_tc_3751_007_compact_lineage(self):
        record = ProvenanceBuilder().runtime_inference(
            block_id="compact:summary:1",
            source_id="compact_snapshot:abc123",
            reason="compact_state_restored_from_records",
            confidence=0.8,
            injected_by="compact_projection",
            cognitive_scope="technical_progress",
        )
        compact_record = record.__class__(**{**record.to_dict(), "source_type": ContextSourceType.COMPACT_STATE.value, "retrieval_reason": tuple(record.retrieval_reason), "excluded_domains": tuple(record.excluded_domains), "inferred": False})

        self.assertEqual(compact_record.source_type, ContextSourceType.COMPACT_STATE.value)
        self.assertEqual(compact_record.source_id, "compact_snapshot:abc123")
        self.assertTrue(ProvenanceValidator().validate_record(compact_record).valid)

    def test_tc_3751_008_resurrection_lineage(self):
        record = ProvenanceBuilder().runtime_inference(
            block_id="resurrection:session_state",
            source_id="session_state:conv_previous",
            reason="session_resurrection_restored_state",
            confidence=0.86,
            injected_by="session_projection",
            cognitive_scope="technical_progress",
        )
        restored = record.__class__(**{**record.to_dict(), "source_type": ContextSourceType.SESSION_STATE.value, "retrieval_reason": tuple(record.retrieval_reason), "excluded_domains": tuple(record.excluded_domains), "inferred": False})

        self.assertEqual(restored.source_type, ContextSourceType.SESSION_STATE.value)
        self.assertEqual(restored.injected_by, "session_projection")
        self.assertTrue(ProvenanceValidator().validate_record(restored).valid)

    def test_tc_3751_009_provider_independence(self):
        builder = ProvenanceBuilder()
        a = builder.from_ranked_evidence(ranked(), cognitive_scope="engineering_collaboration")
        b = builder.from_ranked_evidence(ranked(), cognitive_scope="engineering_collaboration")

        self.assertEqual(a.source_type, b.source_type)
        self.assertEqual(a.source_id, b.source_id)
        self.assertEqual(a.authority, b.authority)
        self.assertEqual(a.injected_by, b.injected_by)

    def test_tc_3751_010_audit_serialization(self):
        builder = ProvenanceBuilder()
        chain = builder.chain([
            builder.current_user(text="current", cognitive_scope="engineering_collaboration"),
            builder.from_ranked_evidence(ranked(), cognitive_scope="engineering_collaboration"),
            builder.exclusion(
                source_id="memory:intimacy",
                source_type=ContextSourceType.GOVERNED_MEMORY.value,
                reason="cognitive_scope_mismatch",
                current_scope="engineering_collaboration",
                blocked_domains=("intimacy",),
            ),
        ], chain_id="audit_test")

        payload = chain.to_dict()
        validation = ProvenanceValidator().validate_chain(chain).to_dict()

        self.assertEqual(payload["chain_id"], "audit_test")
        self.assertEqual(len(payload["records"]), 3)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["records_checked"], 3)

    def test_tc_3751_011_semantic_retriever_emits_provenance_chain(self):
        _section, meta = SemanticContextRetriever(ROOT).prompt_section("上一轮 E2E Alpha 单轮受治理 E2E", limit=3)

        self.assertIn("provenance_chain", meta)
        self.assertIn("provenance_validation", meta)
        self.assertTrue(meta["provenance_validation"]["valid"])
        self.assertLessEqual(len(meta["provenance_chain"]["records"]), 3)


if __name__ == "__main__":
    unittest.main()
