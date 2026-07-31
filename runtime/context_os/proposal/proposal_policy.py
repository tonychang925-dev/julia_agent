from __future__ import annotations

from dataclasses import dataclass

from .state_proposal import ProposalType, StateProposal


@dataclass(frozen=True)
class ProposalDecision:
    proposal: StateProposal
    accepted: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal.proposal_id,
            "proposal_type": self.proposal.proposal_type.value,
            "accepted": self.accepted,
            "reason": self.reason,
        }


@dataclass
class ProposalPolicy:
    """Authority boundary for async worker proposals."""

    min_confidence: float = 0.55
    protected_targets: frozenset[str] = frozenset({"identity", "relationship", "persona"})
    direct_mutation_types: frozenset[ProposalType] = frozenset(
        {ProposalType.SESSION_STATE_UPDATE, ProposalType.TASK_STATE_UPDATE, ProposalType.EVIDENCE_GAP}
    )

    def decide(self, proposal: StateProposal) -> ProposalDecision:
        if proposal.target in self.protected_targets:
            return ProposalDecision(proposal, False, "protected_field_runtime_authority_required")
        if proposal.confidence < self.min_confidence:
            return ProposalDecision(proposal, False, "confidence_below_threshold")
        if proposal.proposal_type in {ProposalType.MEMORY_CANDIDATE, ProposalType.COMPACT_CANDIDATE}:
            return ProposalDecision(proposal, True, "accepted_as_candidate_only_no_direct_mutation")
        if proposal.proposal_type in self.direct_mutation_types:
            return ProposalDecision(proposal, True, "accepted_for_governed_mutation")
        return ProposalDecision(proposal, False, "unsupported_proposal_type")
