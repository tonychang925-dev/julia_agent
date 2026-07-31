from __future__ import annotations

from pathlib import Path

from runtime.cognitive.arbitration import ArbitrationContext, ContextArbitrator
from runtime.conversation_state import ContinuityManager
from runtime.memory import MemoryRuntime
from runtime.memory.retrieval import MemoryRetrievalContext
from runtime.persona import PersonaCompiler, PersonaLoader
from runtime.relationship import RelationshipRuntime
from runtime.situation import SituationRuntime

from .context_policy import ContextPolicy
from .julia_context import CognitiveTurn, JuliaContext, RuntimeEnvelope
from .memory_selector import MemorySelector


class ContextCompiler:
    """Compiles Phase 3.5 cognitive runtime inputs into JuliaContext v4."""

    def __init__(self, project_root: str | Path, *, policy: ContextPolicy | None = None):
        self.project_root = Path(project_root)
        self.policy = policy or ContextPolicy()
        self.persona_loader = PersonaLoader(self.project_root)
        self.persona_compiler = PersonaCompiler()
        self.relationship_runtime = RelationshipRuntime(self.project_root)
        self.memory_runtime = MemoryRuntime(self.project_root)
        self.memory_selector = MemorySelector(self.memory_runtime)
        self.situation_runtime = SituationRuntime(self.project_root)
        self.context_arbitrator = ContextArbitrator()
        self.continuity_manager = ContinuityManager()
        self.last_memory_trace: dict[str, object] = {"retrieved": []}

    def compile(
        self,
        runtime_envelope: RuntimeEnvelope,
        user_input: str,
        *,
        conversation_context: dict[str, object] | None = None,
        user_intent: dict[str, object] | None = None,
    ) -> CognitiveTurn:
        persona_context = self.persona_compiler.compile(self.persona_loader.load())
        relationship_context = self.relationship_runtime.build_context()
        conversation_source = dict(conversation_context or {})
        raw_recent_turns = conversation_source.get("recent_turns")
        recent_turns = raw_recent_turns if isinstance(raw_recent_turns, list) else []
        previous_state = conversation_source.get("conversation_state")
        preview_conversation_context = self.continuity_manager.build_context(
            previous_state=previous_state if isinstance(previous_state, dict) or previous_state is not None else None,
            recent_turns=recent_turns,
            current_user_input=user_input,
        )
        base_situation_context = self.situation_runtime.build_context()
        arbitration_context = {
            **conversation_source,
            "active_topics": preview_conversation_context.active_topics,
            "current_arc": preview_conversation_context.current_arc,
        }
        if preview_conversation_context.recent_turns:
            last_mode = preview_conversation_context.recent_turns[-1].cognitive_mode
            if last_mode:
                arbitration_context.setdefault("recent_cognitive_mode", last_mode)
        arbitration = self.context_arbitrator.decide(
            ArbitrationContext(
                relationship_context=relationship_context,
                situation_context=base_situation_context,
                conversation_context=arbitration_context,
                recent_turns=[turn.to_recent_dict() for turn in preview_conversation_context.recent_turns],
                user_intent={"user_input": user_input, **dict(user_intent or {})},
            )
        )
        situation_context = self.situation_runtime.build_context(arbitration.mode.name)
        continuity_context = self.continuity_manager.build_context(
            previous_state=previous_state if isinstance(previous_state, dict) or previous_state is not None else None,
            recent_turns=recent_turns,
            current_user_input=user_input,
            cognitive_mode=arbitration.mode.name,
        )
        memory_retrieval_context = MemoryRetrievalContext(
            user_input=user_input,
            active_topics=continuity_context.active_topics,
            current_arc=continuity_context.current_arc,
            cognitive_mode=arbitration.mode.name,
            relationship_stage=relationship_context.relationship_stage,
        )
        memory_explanations = self.memory_runtime.retrieve_with_explanations(
            memory_retrieval_context,
            limit=self.policy.memory_limit,
        )
        memory_context = [item.memory for item in memory_explanations]
        self.last_memory_trace = {
            "retrieved": [
                {
                    "id": item.memory.id,
                    "type": item.memory.type,
                    "summary": item.memory.summary,
                    "topics": item.memory.topics,
                    "score": item.score,
                    "reason": item.reason,
                    "components": item.components,
                }
                for item in memory_explanations
            ]
        }
        julia_context = JuliaContext(
            persona_context=persona_context,
            relationship_context=relationship_context,
            memory_context=memory_context,
            situation_context=situation_context,
            conversation_context=continuity_context,
            cognitive_mode=arbitration.to_context(),
            user_input=user_input,
        )
        return CognitiveTurn(runtime_envelope=runtime_envelope, julia_context=julia_context)
