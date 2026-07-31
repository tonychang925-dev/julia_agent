from __future__ import annotations

from dataclasses import dataclass, field

from runtime.context_os.planner.context_plan import ContextPlan

from .budget_policy import BudgetPolicy
from .context_block import ContextBlock


@dataclass(frozen=True)
class BudgetAllocation:
    plan_id: str
    target_budget_tokens: int
    effective_budget_tokens: int
    allocated_tokens: int
    included_blocks: list[ContextBlock] = field(default_factory=list)
    excluded_blocks: list[ContextBlock] = field(default_factory=list)
    clipped_blocks: list[str] = field(default_factory=list)
    required_overflow: bool = False

    @property
    def budget_utilization(self) -> float:
        if self.effective_budget_tokens <= 0:
            return 1.0
        return min(1.0, self.allocated_tokens / self.effective_budget_tokens)

    def to_trace(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "target_budget_tokens": self.target_budget_tokens,
            "effective_budget_tokens": self.effective_budget_tokens,
            "allocated_tokens": self.allocated_tokens,
            "budget_utilization": self.budget_utilization,
            "included_blocks": [b.block_id for b in self.included_blocks],
            "excluded_blocks": [{"block_id": b.block_id, "reason": b.exclusion_reason} for b in self.excluded_blocks],
            "clipped_blocks": self.clipped_blocks,
            "required_overflow": self.required_overflow,
        }


@dataclass
class ContextBudgetManager:
    policy: BudgetPolicy = field(default_factory=BudgetPolicy)

    def allocate(self, *, plan: ContextPlan, blocks: list[ContextBlock]) -> BudgetAllocation:
        effective_budget = self.policy.effective_budget(plan)
        boosts = self.policy.priority_boosts(plan.intent_type)

        def sort_key(block: ContextBlock) -> tuple[int, int, int]:
            boosted = block.priority + boosts.get(str(block.block_type), 0)
            return (1 if block.required else 0, boosted, -block.token_count)

        required_blocks = [b for b in blocks if b.required or str(b.block_type) in plan.required_blocks]
        optional_blocks = [b for b in blocks if b not in required_blocks]
        ordered = sorted(required_blocks, key=sort_key, reverse=True) + sorted(optional_blocks, key=sort_key, reverse=True)

        included: list[ContextBlock] = []
        excluded: list[ContextBlock] = []
        clipped: list[str] = []
        allocated = 0
        required_overflow = False

        for block in ordered:
            if not block.included:
                excluded.append(block)
                continue
            if str(block.block_type) in plan.excluded_blocks or block.block_id in plan.excluded_blocks:
                excluded.append(block.exclude("excluded_by_context_plan"))
                continue

            token_count = block.token_count
            remaining = effective_budget - allocated
            is_required = block.required or str(block.block_type) in plan.required_blocks

            if token_count <= remaining:
                included.append(block.include())
                allocated += token_count
                continue

            if is_required:
                overflow_limit = int(effective_budget * self.policy.max_required_overflow_ratio)
                if allocated + token_count <= overflow_limit:
                    included.append(block.include())
                    allocated += token_count
                    required_overflow = allocated > effective_budget
                    continue
                clipped_tokens = max(1, remaining) if remaining > 0 else max(1, effective_budget - allocated)
                clipped_block = block.clipped_to_tokens(max(1, clipped_tokens)).include()
                included.append(clipped_block)
                allocated += clipped_block.token_count
                clipped.append(block.block_id)
                required_overflow = allocated > effective_budget
                continue

            excluded.append(block.exclude("budget_exceeded"))

        return BudgetAllocation(
            plan_id=plan.plan_id,
            target_budget_tokens=plan.target_budget_tokens,
            effective_budget_tokens=effective_budget,
            allocated_tokens=allocated,
            included_blocks=included,
            excluded_blocks=excluded,
            clipped_blocks=clipped,
            required_overflow=required_overflow,
        )
