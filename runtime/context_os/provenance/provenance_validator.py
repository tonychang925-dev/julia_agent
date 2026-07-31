from __future__ import annotations

from dataclasses import dataclass

from .provenance_chain import ContextProvenanceChain
from .provenance_decision import ProvenanceValidationDecision
from .provenance_record import ContextProvenanceRecord
from .provenance_type import ContextSourceType


@dataclass(frozen=True)
class ProvenanceValidator:
    def validate_record(self, record: ContextProvenanceRecord) -> ProvenanceValidationDecision:
        errors: list[str] = []
        warnings: list[str] = []
        required = {
            "provenance_id": record.provenance_id,
            "context_block_id": record.context_block_id,
            "source_type": record.source_type,
            "source_id": record.source_id,
            "injected_by": record.injected_by,
            "created_at": record.created_at,
        }
        for key, value in required.items():
            if not value:
                errors.append(f"missing_{key}")
        if record.source_type not in {item.value for item in ContextSourceType}:
            errors.append("unknown_source_type")
        if record.source_type == ContextSourceType.PROVIDER_OUTPUT.value and record.speaker == "Tony":
            errors.append("provider_output_cannot_speak_as_tony")
        if record.inferred and record.source_type != ContextSourceType.RUNTIME_INFERENCE.value:
            errors.append("inference_must_use_runtime_inference_source_type")
        if record.source_type == ContextSourceType.RUNTIME_INFERENCE.value and record.authority > 0.2:
            errors.append("runtime_inference_authority_too_high")
        if record.source_type == ContextSourceType.CURRENT_USER.value and record.speaker != "Tony":
            errors.append("current_user_must_be_tony")
        if not record.retrieval_reason:
            warnings.append("missing_retrieval_reason")
        return ProvenanceValidationDecision(not errors, errors, warnings, records_checked=1)

    def validate_chain(self, chain: ContextProvenanceChain) -> ProvenanceValidationDecision:
        errors: list[str] = []
        warnings: list[str] = []
        seen_blocks: set[str] = set()
        for record in chain.records:
            decision = self.validate_record(record)
            errors.extend(decision.errors)
            warnings.extend(decision.warnings)
            if record.decision == "included":
                seen_blocks.add(record.context_block_id)
        if not seen_blocks:
            warnings.append("no_included_context_blocks")
        return ProvenanceValidationDecision(not errors, errors, warnings, records_checked=len(chain.records))
