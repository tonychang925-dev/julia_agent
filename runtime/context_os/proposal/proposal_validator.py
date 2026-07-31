from __future__ import annotations

from dataclasses import dataclass, field

from .proposal_policy import ProposalDecision, ProposalPolicy
from .state_proposal import ProposalType, StateProposal


@dataclass(frozen=True)
class ProposalValidationResult:
    proposals: list[StateProposal]
    decisions: list[ProposalDecision]

    @property
    def accepted(self) -> list[StateProposal]:
        return [d.proposal for d in self.decisions if d.accepted]

    @property
    def rejected(self) -> list[StateProposal]:
        return [d.proposal for d in self.decisions if not d.accepted]

    @property
    def mutation_ready(self) -> list[StateProposal]:
        return [
            d.proposal
            for d in self.decisions
            if d.accepted
            and d.proposal.proposal_type
            in {ProposalType.SESSION_STATE_UPDATE, ProposalType.TASK_STATE_UPDATE, ProposalType.EVIDENCE_GAP}
        ]

    @property
    def candidate_only(self) -> list[StateProposal]:
        return [
            d.proposal
            for d in self.decisions
            if d.accepted
            and d.proposal.proposal_type in {ProposalType.MEMORY_CANDIDATE, ProposalType.COMPACT_CANDIDATE}
        ]


@dataclass
class ProposalValidator:
    policy: ProposalPolicy = field(default_factory=ProposalPolicy)

    def validate(self, proposals: list[StateProposal]) -> ProposalValidationResult:
        return ProposalValidationResult(
            proposals=list(proposals),
            decisions=[self.policy.decide(proposal) for proposal in proposals],
        )
