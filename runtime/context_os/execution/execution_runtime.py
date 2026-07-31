from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from runtime.context_os.budget import ContextBlock
from runtime.context_os.projection import ContextProjectionInputs
from runtime.context_os.mutation import ContextMutationRuntime, ContextWorkingState

from .context_turn import ContextTurn
from .execution_trace import ExecutionTrace
from .post_turn_processor import PostTurnProcessor
from .pre_turn_processor import PreTurnProcessor


class ProviderCallable(Protocol):
    def __call__(self, *, user_input: str, context_blocks: list[ContextBlock]) -> str: ...


@dataclass
class ContextExecutionRuntime:
    pre_turn: PreTurnProcessor = field(default_factory=PreTurnProcessor)
    post_turn: PostTurnProcessor = field(default_factory=PostTurnProcessor)
    mutation_runtime: ContextMutationRuntime = field(default_factory=ContextMutationRuntime)

    def run_turn(
        self,
        *,
        session_id: str,
        user_input: str,
        candidate_blocks: list[ContextBlock] | None = None,
        projection_inputs: ContextProjectionInputs | None = None,
        provider: ProviderCallable | None = None,
        cognitive_mode: str = "conversation",
        provider_request_id: str | None = None,
        provider_latency_ms: int | None = None,
        working_state: ContextWorkingState | None = None,
    ) -> ContextTurn:
        pre = self.pre_turn.process(
            user_input=user_input,
            cognitive_mode=cognitive_mode,
            candidate_blocks=candidate_blocks or [],
            projection_inputs=projection_inputs,
        )
        turn = ContextTurn.create(
            session_id=session_id,
            user_input=user_input,
            context_plan=pre.plan,
            selected_blocks=pre.selected_blocks,
            quality=pre.quality,
            metadata={"budget_trace": pre.budget_trace, "excluded_sources": pre.excluded_sources},
        )
        response = provider(user_input=user_input, context_blocks=pre.selected_blocks) if provider else ""
        mutations = self.post_turn.process(turn=turn, response=response)
        state_transition = None
        if working_state is not None:
            state_transition = self.mutation_runtime.process_turn(state=working_state, turn=turn.complete(response=response, mutations=mutations, trace=ExecutionTrace.create(
                turn_id=turn.turn_id,
                session_id=session_id,
                plan_id=pre.plan.plan_id,
                context_block_ids=[b.block_id for b in pre.selected_blocks],
                evidence_refs=[ref for b in pre.selected_blocks for ref in b.evidence_ids],
                excluded_sources=pre.excluded_sources,
                budget_trace=pre.budget_trace,
                quality=pre.quality,
                provider_request_id=provider_request_id,
                provider_latency_ms=provider_latency_ms,
                mutations=mutations,
            )))
        trace = ExecutionTrace.create(
            turn_id=turn.turn_id,
            session_id=session_id,
            plan_id=pre.plan.plan_id,
            context_block_ids=[b.block_id for b in pre.selected_blocks],
            evidence_refs=[ref for b in pre.selected_blocks for ref in b.evidence_ids],
            excluded_sources=pre.excluded_sources,
            budget_trace=pre.budget_trace,
            quality=pre.quality,
            provider_request_id=provider_request_id,
            provider_latency_ms=provider_latency_ms,
            mutations=mutations,
        )
        completed = turn.complete(
            response=response,
            mutations=mutations,
            trace=trace,
            provider_request_id=provider_request_id,
        )
        if state_transition is not None:
            completed = completed.__class__(**{**completed.__dict__, "metadata": {**completed.metadata, "mutation_state_transition": {
                "events": [event.to_dict() for event in state_transition.events],
                "decisions": [decision.to_dict() for decision in state_transition.decisions],
                "previous_state": state_transition.previous_state.to_dict(),
                "next_state": state_transition.next_state.to_dict(),
            }}})
        return completed
