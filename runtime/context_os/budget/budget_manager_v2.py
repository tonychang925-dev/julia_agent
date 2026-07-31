from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

from runtime.context_os.planner.context_plan import ContextPlan

from .budget_allocator import BudgetAllocation, ContextBudgetManager
from .budget_policy import BudgetPolicy
from .context_block import ContextBlock


class BudgetPressureLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class BudgetEnvelope:
    """Effective context-window envelope used before compact execution.

    v2 separates measurement and preparation from actual compact execution:
    - hard_limit_tokens is the external model/context limit.
    - target_budget_tokens comes from the ContextPlan.
    - reserve_tail_tokens is protected for recent turns / preserve-tail strategy.
    - safety_margin_tokens is unavailable by policy.
    """

    hard_limit_tokens: int
    target_budget_tokens: int
    effective_budget_tokens: int
    reserve_tail_tokens: int
    safety_margin_tokens: int

    @property
    def allocatable_tokens(self) -> int:
        return max(1, self.effective_budget_tokens - self.reserve_tail_tokens)

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class BudgetPressure:
    measured_tokens: int
    projected_tokens: int
    effective_budget_tokens: int
    hard_limit_tokens: int
    utilization: float
    projected_utilization: float
    level: BudgetPressureLevel
    should_prepare_compact: bool

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["level"] = self.level.value
        return data


@dataclass(frozen=True)
class CompactPreparationCandidate:
    """Candidate signal for compact runtime; does not execute compact."""

    candidate_id: str
    reason: str
    source_block_ids: list[str] = field(default_factory=list)
    estimated_reclaim_tokens: int = 0
    urgency: BudgetPressureLevel = BudgetPressureLevel.NORMAL

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["urgency"] = self.urgency.value
        return data


@dataclass(frozen=True)
class BudgetAllocationV2:
    allocation: BudgetAllocation
    envelope: BudgetEnvelope
    pressure: BudgetPressure
    preserve_tail_block_ids: list[str] = field(default_factory=list)
    compact_candidates: list[CompactPreparationCandidate] = field(default_factory=list)

    @property
    def compact_preparation_needed(self) -> bool:
        return bool(self.compact_candidates)

    @property
    def included_blocks(self) -> list[ContextBlock]:
        return self.allocation.included_blocks

    @property
    def excluded_blocks(self) -> list[ContextBlock]:
        return self.allocation.excluded_blocks

    def to_trace(self) -> dict[str, object]:
        trace = self.allocation.to_trace()
        trace.update(
            {
                "budget_envelope": self.envelope.to_dict(),
                "budget_pressure": self.pressure.to_dict(),
                "preserve_tail_block_ids": self.preserve_tail_block_ids,
                "compact_preparation_needed": self.compact_preparation_needed,
                "compact_candidates": [candidate.to_dict() for candidate in self.compact_candidates],
                "compact_executed": False,
            }
        )
        return trace


@dataclass(frozen=True)
class BudgetPolicyV2(BudgetPolicy):
    hard_limit_tokens: int = 16000
    preserve_tail_ratio: float = 0.18
    min_preserve_tail_tokens: int = 256
    max_preserve_tail_tokens: int = 2048
    high_pressure_ratio: float = 0.82
    critical_pressure_ratio: float = 0.94
    compact_reclaim_min_tokens: int = 512

    def envelope(self, plan: ContextPlan) -> BudgetEnvelope:
        effective = self.effective_budget(plan)
        safety = max(0, int(plan.target_budget_tokens * self.safety_margin_ratio))
        tail = int(effective * self.preserve_tail_ratio)
        reserve_tail = min(self.max_preserve_tail_tokens, max(self.min_preserve_tail_tokens, tail))
        reserve_tail = min(max(1, effective - 1), reserve_tail)
        return BudgetEnvelope(
            hard_limit_tokens=self.hard_limit_tokens,
            target_budget_tokens=plan.target_budget_tokens,
            effective_budget_tokens=effective,
            reserve_tail_tokens=reserve_tail,
            safety_margin_tokens=safety,
        )

    def pressure(self, *, measured_tokens: int, projected_tokens: int, envelope: BudgetEnvelope) -> BudgetPressure:
        utilization = measured_tokens / envelope.effective_budget_tokens if envelope.effective_budget_tokens else 1.0
        projected_utilization = projected_tokens / envelope.effective_budget_tokens if envelope.effective_budget_tokens else 1.0
        ratio = max(utilization, projected_utilization)
        if ratio >= self.critical_pressure_ratio:
            level = BudgetPressureLevel.CRITICAL
        elif ratio >= self.high_pressure_ratio:
            level = BudgetPressureLevel.HIGH
        elif ratio >= 0.55:
            level = BudgetPressureLevel.NORMAL
        else:
            level = BudgetPressureLevel.LOW
        return BudgetPressure(
            measured_tokens=measured_tokens,
            projected_tokens=projected_tokens,
            effective_budget_tokens=envelope.effective_budget_tokens,
            hard_limit_tokens=envelope.hard_limit_tokens,
            utilization=utilization,
            projected_utilization=projected_utilization,
            level=level,
            should_prepare_compact=level in {BudgetPressureLevel.HIGH, BudgetPressureLevel.CRITICAL},
        )


@dataclass
class ContextBudgetManagerV2:
    policy: BudgetPolicyV2 = field(default_factory=BudgetPolicyV2)

    def measure(self, *, plan: ContextPlan, blocks: list[ContextBlock]) -> BudgetPressure:
        envelope = self.policy.envelope(plan)
        measured = sum(block.token_count for block in blocks if block.included)
        projected = measured + envelope.reserve_tail_tokens
        return self.policy.pressure(measured_tokens=measured, projected_tokens=projected, envelope=envelope)

    def allocate(self, *, plan: ContextPlan, blocks: list[ContextBlock]) -> BudgetAllocationV2:
        envelope = self.policy.envelope(plan)
        pressure = self.measure(plan=plan, blocks=blocks)
        tail_blocks = self._tail_blocks(blocks)
        preserve_tail_ids = [block.block_id for block in tail_blocks]

        alloc_plan = type(plan)(**{**plan.__dict__, "target_budget_tokens": envelope.allocatable_tokens})
        boosted_blocks = self._with_tail_preserved(blocks, preserve_tail_ids)
        allocation = ContextBudgetManager(policy=self.policy).allocate(plan=alloc_plan, blocks=boosted_blocks)

        candidates = self._compact_candidates(pressure=pressure, blocks=blocks, allocation=allocation)
        return BudgetAllocationV2(
            allocation=allocation,
            envelope=envelope,
            pressure=pressure,
            preserve_tail_block_ids=preserve_tail_ids,
            compact_candidates=candidates,
        )

    def _tail_blocks(self, blocks: list[ContextBlock]) -> list[ContextBlock]:
        candidates = [
            block
            for block in blocks
            if str(block.block_type) == "recent_turns" or block.metadata.get("preserve_tail") is True
        ]
        candidates.sort(key=lambda block: int(block.metadata.get("tail_index", 0) or 0))
        return candidates[-3:]

    def _with_tail_preserved(self, blocks: list[ContextBlock], preserve_tail_ids: list[str]) -> list[ContextBlock]:
        preserved = set(preserve_tail_ids)
        result: list[ContextBlock] = []
        for block in blocks:
            if block.block_id in preserved:
                result.append(
                    ContextBlock(
                        block_id=block.block_id,
                        block_type=block.block_type,
                        priority=max(block.priority, 95),
                        content=block.content,
                        required=True,
                        estimated_tokens=block.estimated_tokens,
                        source_refs=block.source_refs,
                        evidence_ids=block.evidence_ids,
                        authority_score=block.authority_score,
                        included=block.included,
                        exclusion_reason=block.exclusion_reason,
                        metadata={**block.metadata, "preserve_tail": True},
                    )
                )
            else:
                result.append(block)
        return result

    def _compact_candidates(
        self,
        *,
        pressure: BudgetPressure,
        blocks: list[ContextBlock],
        allocation: BudgetAllocation,
    ) -> list[CompactPreparationCandidate]:
        if not pressure.should_prepare_compact:
            return []

        excluded_ids = {block.block_id for block in allocation.excluded_blocks}
        compactable = [
            block
            for block in blocks
            if block.block_id in excluded_ids
            or str(block.block_type) in {"semantic_evidence", "compact_state", "open_loops", "recent_turns"}
        ]
        reclaim = sum(block.token_count for block in compactable if not block.required)
        if reclaim < self.policy.compact_reclaim_min_tokens:
            return []
        return [
            CompactPreparationCandidate(
                candidate_id=f"compact_candidate_{allocation.plan_id}",
                reason="budget_pressure_prepare_only",
                source_block_ids=[block.block_id for block in compactable],
                estimated_reclaim_tokens=reclaim,
                urgency=pressure.level,
            )
        ]
