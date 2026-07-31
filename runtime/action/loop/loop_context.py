from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from runtime.cognitive.context_compiler import JuliaContext


class ContextMutationAdapter(Protocol):
    def mutate_after_step(self, context: JuliaContext, step_trace: object) -> JuliaContext: ...


@dataclass(frozen=True)
class IdentityContextMutationAdapter:
    """Default test-safe adapter: returns the context object unchanged.

    The explicit adapter boundary prevents the loop from silently reusing old
    prompt state in integrations that provide a real Context OS mutation runtime.
    """

    def mutate_after_step(self, context: JuliaContext, step_trace: object) -> JuliaContext:
        return context


@dataclass(frozen=True)
class CognitiveLoopContext:
    julia_context: JuliaContext
    context_mutation_adapter: ContextMutationAdapter = IdentityContextMutationAdapter()
