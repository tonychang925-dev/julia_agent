from __future__ import annotations

from dataclasses import dataclass, field

from runtime.context_os.budget import ContextBlock, ContextBudgetManager
from runtime.context_os.planner import ContextPlan, ContextPlanner
from runtime.context_os.quality import ContextQuality, ContextQualityEvaluator
from runtime.context_os.projection import ContextProjectionInputs, ContextProjector
from runtime.context_os.conflict import ContextConflictResolver


@dataclass(frozen=True)
class PreTurnResult:
    plan: ContextPlan
    selected_blocks: list[ContextBlock]
    quality: ContextQuality
    budget_trace: dict[str, object]
    excluded_sources: list[str]


@dataclass
class PreTurnProcessor:
    planner: ContextPlanner = field(default_factory=ContextPlanner)
    budget_manager: ContextBudgetManager = field(default_factory=ContextBudgetManager)
    quality_evaluator: ContextQualityEvaluator = field(default_factory=ContextQualityEvaluator)
    projector: ContextProjector = field(default_factory=ContextProjector)
    conflict_resolver: ContextConflictResolver = field(default_factory=ContextConflictResolver)

    def process(
        self,
        *,
        user_input: str,
        cognitive_mode: str = "conversation",
        candidate_blocks: list[ContextBlock] | None = None,
        projection_inputs: ContextProjectionInputs | None = None,
    ) -> PreTurnResult:
        plan = self.planner.plan(user_input, cognitive_mode=cognitive_mode)
        blocks = list(candidate_blocks or [])
        projection_trace = None
        if projection_inputs is not None:
            projection = self.projector.project(plan=plan, inputs=projection_inputs)
            blocks = [*projection.blocks, *blocks]
            projection_trace = projection.trace
        blocks, conflict_resolutions = self.conflict_resolver.resolve_blocks(blocks)
        allocation = self.budget_manager.allocate(plan=plan, blocks=blocks)
        selected = allocation.included_blocks
        quality = self.quality_evaluator.evaluate(plan=plan, blocks=selected)
        excluded_sources = [
            ref
            for block in allocation.excluded_blocks
            for ref in (block.source_refs or [block.block_id])
        ]
        return PreTurnResult(
            plan=plan,
            selected_blocks=selected,
            quality=quality,
            budget_trace={**allocation.to_trace(), **({"context_projection": projection_trace} if projection_trace else {}), "conflict_resolutions": [r.to_dict() for r in conflict_resolutions]},
            excluded_sources=excluded_sources,
        )
