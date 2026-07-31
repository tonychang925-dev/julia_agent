from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone

from runtime.cognitive.context_builder import ContextBuilder
from runtime.cognitive.context_compiler import ContextCompiler, ContextPolicy, RuntimeEnvelope
from runtime.cognitive.context_validation import ContextValidator
from runtime.cognitive.rendering import CognitiveRenderer, ProviderFormatter
from runtime.cognitive.provider.echo_provider import EchoProvider
from runtime.cognitive.provider.deepseek_provider import DeepSeekProvider
from runtime.cognitive.provider.codex_cli_provider import CodexCLIProvider
from runtime.cognitive.provider.llm_provider import LLMProvider
from runtime.persona.behavior_policy import contract_for_mode
from runtime.persona.provider_alignment import ProviderBehaviorAdapter
from runtime.cognitive.short_greeting import ShortGreetingResponder
from runtime.cognitive.vocal_gesture import VocalGestureResponder
from runtime.conversation_state import ConversationContinuityContext, ConversationTurn, ContinuityManager, TopicTracker
from runtime.conversation_runtime.voice_latency_policy import VoiceLatencyPolicy
from runtime.action import ActionGovernanceLayer, ActionPlanner, ActionPolicy, ActionReflectionEngine, AutonomousCognitiveLoop
from runtime.context_assembly import ContextAssemblyEngine
from runtime.response_quality import AnswerCoverageGate
from runtime.action.action_executor import ActionExecutor
from runtime.capability import CapabilityRouter

from .cognitive_bridge import CognitiveBridge, CognitiveChunk, CognitiveResponse


@dataclass
class DirectLLMBridge(CognitiveBridge):
    """CognitiveBridge backed by Julia Runtime's own LLMProvider.

    This is the host-independent bridge path. ClaudeCodeBridge remains available
    as a host/tool bridge, while DirectLLMBridge uses JuliaContext directly.
    """

    project_root: Path
    provider: LLMProvider
    current_backend: str = "direct_llm"
    short_greeting_enabled: bool = True
    vocal_gesture_enabled: bool = True
    relationship_mode: str | None = None
    voice_latency_optimized: bool = False
    voice_max_tokens: int = 320
    action_loop_enabled: bool = False
    action_loop: AutonomousCognitiveLoop | None = None

    @classmethod
    def echo(
        cls,
        project_root: str | Path,
        *,
        action_loop_enabled: bool = False,
        action_loop: AutonomousCognitiveLoop | None = None,
    ) -> "DirectLLMBridge":
        return cls(
            project_root=Path(project_root),
            provider=EchoProvider(),
            current_backend="echo_provider",
            action_loop_enabled=action_loop_enabled,
            action_loop=action_loop,
        )

    @classmethod
    def deepseek(
        cls,
        project_root: str | Path,
        *,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        short_greeting_enabled: bool = True,
        vocal_gesture_enabled: bool = True,
        relationship_mode: str | None = None,
        voice_latency_optimized: bool = False,
        voice_max_tokens: int = 320,
        action_loop_enabled: bool = False,
        action_loop: AutonomousCognitiveLoop | None = None,
    ) -> "DirectLLMBridge":
        return cls(
            project_root=Path(project_root),
            provider=DeepSeekProvider(api_key=api_key, model=model, max_tokens=voice_max_tokens if voice_latency_optimized else None, temperature=0.5 if voice_latency_optimized else None),
            current_backend="deepseek_provider",
            short_greeting_enabled=short_greeting_enabled,
            vocal_gesture_enabled=vocal_gesture_enabled,
            relationship_mode=relationship_mode,
            voice_latency_optimized=voice_latency_optimized,
            voice_max_tokens=voice_max_tokens,
            action_loop_enabled=action_loop_enabled,
            action_loop=action_loop,
        )


    @classmethod
    def codex(
        cls,
        project_root: str | Path,
        *,
        model: str | None = None,
        timeout_s: float = 120.0,
        codex_bin: str = "codex",
        short_greeting_enabled: bool = True,
        vocal_gesture_enabled: bool = True,
        relationship_mode: str | None = None,
        voice_latency_optimized: bool = False,
        voice_max_tokens: int = 320,
        action_loop_enabled: bool = False,
        action_loop: AutonomousCognitiveLoop | None = None,
    ) -> "DirectLLMBridge":
        return cls(
            project_root=Path(project_root),
            provider=CodexCLIProvider(project_root=Path(project_root), model=model, timeout_s=timeout_s, codex_bin=codex_bin),
            current_backend="codex_cli_provider",
            short_greeting_enabled=short_greeting_enabled,
            vocal_gesture_enabled=vocal_gesture_enabled,
            relationship_mode=relationship_mode,
            voice_latency_optimized=voice_latency_optimized,
            voice_max_tokens=voice_max_tokens,
            action_loop_enabled=action_loop_enabled,
            action_loop=action_loop,
        )

    def __post_init__(self) -> None:
        self.context_builder = ContextBuilder(self.project_root)
        self.context_compiler = ContextCompiler(self.project_root, policy=ContextPolicy(memory_limit=5))
        self.context_validator = ContextValidator(max_memory_items=8)
        self.cognitive_renderer = CognitiveRenderer()
        self.provider_formatter = ProviderFormatter()
        self.provider_behavior_adapter = ProviderBehaviorAdapter()
        self.voice_latency_policy = VoiceLatencyPolicy(enabled=self.voice_latency_optimized, max_tokens=self.voice_max_tokens)
        self.context_assembly_engine = ContextAssemblyEngine(self.project_root)
        self.answer_coverage_gate = AnswerCoverageGate(self.project_root)
        self.short_greeting = ShortGreetingResponder()
        self.action_governance_layer = ActionGovernanceLayer()
        self.vocal_gesture = VocalGestureResponder()
        self._pending: dict[tuple[str, int], tuple[str, float]] = {}
        self._history: dict[str, list[dict[str, str]]] = {}
        self._conversation_states: dict[str, ConversationContinuityContext] = {}
        self._continuity_manager = ContinuityManager()
        self._topic_tracker = TopicTracker()
        if self.action_loop_enabled and self.action_loop is None:
            self.action_loop = AutonomousCognitiveLoop(
                planner=ActionPlanner(),
                policy=ActionPolicy(),
                executor=ActionExecutor(router=CapabilityRouter()),
                reflector=ActionReflectionEngine(),
            )

    def _build_context(self, text: str, *, session_id: str, turn_id: int, policy: dict | None = None):
        return self.context_builder.build(
            text,
            session_id=session_id,
            current_backend=self.current_backend,
            conversation={"session_id": session_id, "turn_id": turn_id, "history": []},
            policy=policy,
        )


    def _runtime_envelope(self, *, session_id: str, turn_id: int) -> RuntimeEnvelope:
        info = self.provider.info()
        return RuntimeEnvelope(
            session_id=session_id,
            turn_id=turn_id,
            provider=info.name,
            backend=info.model,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latency_target_ms=1500,
        )

    def _phase35_messages(self, text: str, *, session_id: str, turn_id: int) -> tuple[list[dict[str, str]], dict[str, object]]:
        envelope = self._runtime_envelope(session_id=session_id, turn_id=turn_id)
        recent_turns = list(self._history.get(session_id, []))[-6:]
        conversation_context = {
            "recent_turns": recent_turns,
            "conversation_state": self._conversation_states.get(session_id),
        }
        user_intent = (
            {"mode": self.relationship_mode, "confidence": 0.99, "source": "explicit_bridge_override"}
            if self.relationship_mode
            else None
        )
        cognitive_turn = self.context_compiler.compile(
            envelope,
            text,
            conversation_context=conversation_context,
            user_intent=user_intent,
        )
        julia_context = cognitive_turn.julia_context
        quality = self.context_validator.validate(julia_context)
        package = self.cognitive_renderer.render(julia_context)
        messages = self.provider_formatter.to_openai_messages(package)
        provider_name = self.provider.info().name
        messages, provider_adaptation = self.provider_behavior_adapter.adapt_messages(
            messages,
            provider=provider_name,
            mode=julia_context.cognitive_mode.mode.name,
        )
        action_loop_trace = self._action_loop_trace(julia_context)
        assembled_context = self.context_assembly_engine.assemble(
            text,
            session_id=session_id,
            julia_context=julia_context,
        )
        if assembled_context.prompt_section and messages:
            messages[0]["content"] = f"{messages[0]['content']}\n\n{assembled_context.prompt_section}"

        behavior_contract = contract_for_mode(julia_context.cognitive_mode.mode.name)
        metadata = {
            "phase35_pipeline": True,
            "behavior_contract": behavior_contract.to_dict(),
            "provider_adaptation": provider_adaptation.to_dict(),
            "cognitive_mode": {
                "name": julia_context.cognitive_mode.mode.name,
                "confidence": julia_context.cognitive_mode.confidence,
                "evidence": julia_context.cognitive_mode.evidence,
                "reason": julia_context.cognitive_mode.reason,
            },
            "context_quality": {
                "passed": quality.passed,
                "errors": quality.errors,
                "warnings": quality.warnings,
                "metrics": quality.metrics,
            },
            "rendering": {
                "system_context_chars": len(package.system_context),
                "memory_summary_chars": len(package.memory_summary),
                "style_constraints_count": len(package.style_constraints),
                "recent_turns_count": len(recent_turns),
            },
            "conversation_continuity": {
                "active_topics": julia_context.conversation_context.active_topics,
                "open_loops": julia_context.conversation_context.open_loops,
                "current_arc": julia_context.conversation_context.current_arc,
                "session_summary": julia_context.conversation_context.session_summary,
            },
            "identity_integrity": {
                "persona": julia_context.persona_context.name,
                "persona_loaded": bool(julia_context.persona_context.name),
                "user": julia_context.relationship_context.user_name,
                "relationship_loaded": bool(julia_context.relationship_context.user_name),
                "memory_loaded": bool(julia_context.memory_context or assembled_context.prompt_section),
                "selected_memory_loaded": bool(julia_context.memory_context),
                "core_identity_memory_loaded": "core_identity_pack" in assembled_context.metadata.get("sections", []),
                "claude_style_memory_loaded": "core_identity_pack" in assembled_context.metadata.get("sections", []),
                "host_dependency": False,
                "source": ["persona_runtime", "relationship_runtime", "memory_runtime", "conversation_runtime", "claude_style_identity_fact_card"],
            },
            "memory_trace": self.context_compiler.last_memory_trace,
            "context_assembly": assembled_context.metadata,
            "action_loop_trace": action_loop_trace,
        }
        messages = self.voice_latency_policy.apply(messages, metadata)
        return messages, metadata


    def _short_greeting_metadata(self, text: str, *, session_id: str, turn_id: int) -> dict[str, object]:
        """Build JuliaContext metadata even when the local greeting short-circuits LLM.

        Short greetings must stay fast and local, but startup turns still need the
        Claude-style always-on memory substrate in trace so Julia does not appear
        to wake without her own memory loaded.
        """
        try:
            _messages, metadata = self._phase35_messages(text, session_id=session_id, turn_id=turn_id)
        except Exception as exc:  # pragma: no cover - greeting must remain available if metadata build fails
            return {
                "phase35_pipeline": False,
                "identity_integrity": {
                    "memory_loaded": False,
                    "host_dependency": False,
                    "source": ["local_short_greeting"],
                },
                "context_assembly": {"enabled": False, "error": str(exc)},
            }
        metadata = dict(metadata)
        metadata["short_greeting_context_loaded"] = True
        return metadata

    def _action_loop_trace(self, julia_context) -> dict[str, object]:
        if not self.action_loop_enabled:
            return {"enabled": False}
        if self.action_loop is None:
            return {"enabled": True, "status": "unavailable", "reason": "action_loop_not_configured"}

        # Phase 3.7.6.1: bridge action entry must use the governed path.
        # The injected action_loop remains the owner of executor/router/reflector
        # wiring, but bridge no longer calls legacy run_once().
        intent = self.action_loop.planner.plan(julia_context)
        governance = self.action_governance_layer.govern(intent, context=julia_context)
        should_execute = bool(intent and governance.decision.decision == "allow")
        execution = self.action_loop.executor.execute_governed(intent, governance) if should_execute else None
        reflection = self.action_loop.reflector.reflect_with_governance(execution) if execution else None
        return {
            "enabled": True,
            "action_path": "governed",
            "governance_layer": "ActionGovernanceLayer",
            "status": self._governed_action_status(intent, governance, execution, reflection),
            "intent": intent.__dict__ if intent else None,
            "decision": governance.decision.to_dict(),
            "governance": {
                "risk": governance.risk.to_dict(),
                "trace": governance.trace.to_dict(),
                "executable": governance.executable,
            },
            "execution": self._governed_execution_summary(intent, execution, reflection),
            "reflection": reflection.to_dict() if reflection else None,
        }

    @staticmethod
    def _governed_action_status(intent, governance, execution, reflection) -> str:
        decision = governance.decision.decision if governance else "reject"
        if intent is None:
            return "no_action"
        if decision == "ask":
            return "awaiting_confirmation"
        if decision == "reject":
            return "rejected"
        if execution is None:
            return "blocked"
        if execution.status == "executed":
            return "completed_with_reflection" if reflection and reflection.candidate else "completed"
        if execution.status == "failed":
            return "failed_with_reflection" if reflection and reflection.candidate else "failed"
        if execution.status == "blocked":
            return "blocked_with_reflection" if reflection and reflection.candidate else "blocked"
        return execution.status

    @staticmethod
    def _governed_execution_summary(intent, execution, reflection) -> dict[str, object] | None:
        if execution is None:
            return None
        tool_result = execution.tool_result
        permission = execution.permission
        return {
            "status": execution.status,
            "capability": intent.required_capability if intent else None,
            "permission_allowed": permission.allowed if permission else None,
            "tool_ok": tool_result.ok if tool_result else None,
            "tool_error": tool_result.error if tool_result else None,
            "reflected": bool(reflection and reflection.candidate),
            "memory_persisted": bool(reflection.persisted) if reflection else False,
        }

    def _remember_turn(self, session_id: str, *, user: str, assistant: str, cognitive_mode: str = "") -> None:
        if not assistant.strip():
            return
        turns = self._history.setdefault(session_id, [])
        turn_id = len(turns) + 1
        turns.append({"user": user, "assistant": assistant, "cognitive_mode": cognitive_mode})
        del turns[:-8]
        turn = ConversationTurn(
            turn_id=turn_id,
            user_text=user,
            assistant_text=assistant,
            timestamp=datetime.now(timezone.utc).isoformat(),
            topics=self._topic_tracker.extract_topics(user, assistant),
            cognitive_mode=cognitive_mode,
            metadata={},
        )
        self._conversation_states[session_id] = self._continuity_manager.update(
            self._conversation_states.get(session_id),
            turn,
        )

    def _provider_supports_phase35_messages(self) -> bool:
        return hasattr(self.provider, "generate_messages") and hasattr(self.provider, "stream_messages")

    def _vocal_gesture_policy(self) -> dict:
        return {
            "language": "Chinese",
            "style": ["brief", "breathy", "vocal", "natural"],
            "response_mode": "vocal_gesture_generation",
            "max_line_count": 1,
            "memory_rule": "do not explain memory/context in this mode",
        }

    def _fallback_vocal_chunk(self, text: str, *, started: float, index: int = 0) -> CognitiveChunk:
        gesture = self.vocal_gesture.match(text)
        fallback_text = gesture.text or "嗯……啊……Tony。"
        return CognitiveChunk(
            text=fallback_text,
            backend="vocal_gesture_fallback",
            index=index,
            is_final=True,
            ok=True,
            metadata={
                "provider": "local_vocal_gesture_fallback",
                "model": "vocal-gesture-fallback-v1",
                "latency_ms": int((perf_counter() - started) * 1000),
                "vocal_gesture": {"matched": True, "reason": gesture.reason or "fallback"},
                "bridge": "direct_llm",
                "fallback": True,
            },
        )

    def send_message(self, text: str, *, session_id: str, turn_id: int) -> None:
        self._pending[(session_id, turn_id)] = (text, perf_counter())

    def receive_response(self, *, session_id: str, turn_id: int) -> CognitiveResponse:
        key = (session_id, turn_id)
        if key not in self._pending:
            return CognitiveResponse(
                text="",
                backend=self.current_backend,
                ok=False,
                error="no pending message for session/turn",
                metadata={"confidence": 0.0},
            )
        text, started = self._pending.pop(key)
        # STT repair: fix common misrecognitions (e.g. "生意"→"呻吟") before LLM sees the text
        text = self.vocal_gesture._repair_stt(text)
        if self.short_greeting_enabled:
            greeting = self.short_greeting.match(text)
            if greeting.matched:
                return CognitiveResponse(
                    text=greeting.text,
                    backend="short_greeting",
                    ok=True,
                    metadata={
                        **self._short_greeting_metadata(text, session_id=session_id, turn_id=turn_id),
                        "provider": "local_short_greeting",
                        "model": "short-greeting-v1",
                        "latency_ms": int((perf_counter() - started) * 1000),
                        "short_greeting": {"matched": True, "reason": greeting.reason},
                        "bridge": "direct_llm",
                    },
                )
        if self._provider_supports_phase35_messages():
            context_started = perf_counter()
            messages, phase35_metadata = self._phase35_messages(text, session_id=session_id, turn_id=turn_id)
            context_finished = perf_counter()
            provider_started = perf_counter()
            response = self.provider.generate_messages(messages)  # type: ignore[attr-defined]
            provider_finished = perf_counter()
            coverage = self.answer_coverage_gate.validate_and_repair(text, response.text)
            response_text = coverage.text
            phase35_metadata = {**phase35_metadata, "answer_coverage": coverage.to_metadata()}
            self._remember_turn(
                session_id,
                user=text,
                assistant=response_text,
                cognitive_mode=str(phase35_metadata.get("cognitive_mode", {}).get("name", "")),
            )
            bridge_timing = {
                "context_build_ms": int((context_finished - context_started) * 1000),
                "provider_call_ms": int((provider_finished - provider_started) * 1000),
                "bridge_total_ms": int((provider_finished - started) * 1000),
            }
            return CognitiveResponse(
                text=response_text,
                backend=response.provider,
                ok=response.ok,
                error=response.error,
                metadata={
                    **response.metadata,
                    **phase35_metadata,
                    "latency_ms": int((perf_counter() - started) * 1000),
                    "bridge": "direct_llm",
                    "bridge_timing": bridge_timing,
                },
            )

        vocal_gesture = self.vocal_gesture.match(text) if self.vocal_gesture_enabled else None
        context_started = perf_counter()
        context = self._build_context(
            text,
            session_id=session_id,
            turn_id=turn_id,
            policy=self._vocal_gesture_policy() if vocal_gesture and vocal_gesture.matched else None,
        )
        context_finished = perf_counter()
        provider_started = perf_counter()
        response = self.provider.generate(context)
        provider_finished = perf_counter()
        if vocal_gesture and vocal_gesture.matched and (not response.ok or not response.text.strip()):
            fallback = self._fallback_vocal_chunk(text, started=started)
            return CognitiveResponse(
                text=fallback.text,
                backend=fallback.backend,
                ok=True,
                metadata=fallback.metadata,
            )
        bridge_timing = {
            "context_build_ms": int((context_finished - context_started) * 1000),
            "provider_call_ms": int((provider_finished - provider_started) * 1000),
            "bridge_total_ms": int((provider_finished - started) * 1000),
        }
        response_metadata_extra = {}
        if vocal_gesture and vocal_gesture.matched:
            response_metadata_extra = {"vocal_gesture_generation": {"matched": True, "reason": vocal_gesture.reason}}
        coverage = self.answer_coverage_gate.validate_and_repair(text, response.text)
        response_text = coverage.text
        self._remember_turn(session_id, user=text, assistant=response_text)
        return CognitiveResponse(
            text=response_text,
            backend=response.provider,
            ok=response.ok,
            error=response.error,
            metadata={
                **response.metadata,
                **response_metadata_extra,
                "answer_coverage": coverage.to_metadata(),
                "latency_ms": int((perf_counter() - started) * 1000),
                "bridge": "direct_llm",
                "bridge_timing": bridge_timing,
                "context_runtime_state": context.runtime_state,
            },
        )

    def stream_response(self, *, session_id: str, turn_id: int) -> Iterator[CognitiveChunk]:
        key = (session_id, turn_id)
        if key not in self._pending:
            yield CognitiveChunk(
                text="",
                backend=self.current_backend,
                index=0,
                is_final=True,
                ok=False,
                error="no pending message for session/turn",
                metadata={"confidence": 0.0},
            )
            return
        text, started = self._pending.pop(key)
        # STT repair: fix common misrecognitions (e.g. "生意"→"呻吟") before LLM sees the text
        text = self.vocal_gesture._repair_stt(text)
        if self.short_greeting_enabled:
            greeting = self.short_greeting.match(text)
            if greeting.matched:
                yield CognitiveChunk(
                    text=greeting.text,
                    backend="short_greeting",
                    index=0,
                    is_final=True,
                    ok=True,
                    metadata={
                        **self._short_greeting_metadata(text, session_id=session_id, turn_id=turn_id),
                        "provider": "local_short_greeting",
                        "model": "short-greeting-v1",
                        "latency_ms": int((perf_counter() - started) * 1000),
                        "short_greeting": {"matched": True, "reason": greeting.reason},
                        "bridge": "direct_llm",
                    },
                )
                return
        if self._provider_supports_phase35_messages():
            context_started = perf_counter()
            messages, phase35_metadata = self._phase35_messages(text, session_id=session_id, turn_id=turn_id)
            context_finished = perf_counter()
            provider_stream_started = perf_counter()
            emitted_text = ""
            for chunk in self.provider.stream_messages(messages):  # type: ignore[attr-defined]
                emitted_text += chunk.text or ""
                now = perf_counter()
                bridge_timing = {
                    "context_build_ms": int((context_finished - context_started) * 1000),
                    "provider_stream_elapsed_ms": int((now - provider_stream_started) * 1000),
                    "bridge_total_ms": int((now - started) * 1000),
                }
                yield CognitiveChunk(
                    text=chunk.text,
                    backend=chunk.provider,
                    index=chunk.index,
                    is_final=chunk.is_final,
                    ok=chunk.ok,
                    error=chunk.error,
                    metadata={
                        **chunk.metadata,
                        **phase35_metadata,
                        "latency_ms": int((perf_counter() - started) * 1000),
                        "bridge": "direct_llm",
                        "bridge_timing": bridge_timing,
                    },
                )
            self._remember_turn(
                session_id,
                user=text,
                assistant=emitted_text,
                cognitive_mode=str(phase35_metadata.get("cognitive_mode", {}).get("name", "")),
            )
            return

        vocal_gesture = self.vocal_gesture.match(text) if self.vocal_gesture_enabled else None
        context_started = perf_counter()
        context = self._build_context(
            text,
            session_id=session_id,
            turn_id=turn_id,
            policy=self._vocal_gesture_policy() if vocal_gesture and vocal_gesture.matched else None,
        )
        context_finished = perf_counter()
        provider_stream_started = perf_counter()
        emitted_text = ""
        for chunk in self.provider.stream(context):
            if vocal_gesture and vocal_gesture.matched and not chunk.ok:
                yield self._fallback_vocal_chunk(text, started=started, index=chunk.index)
                return
            emitted_text += chunk.text or ""
            now = perf_counter()
            bridge_timing = {
                "context_build_ms": int((context_finished - context_started) * 1000),
                "provider_stream_elapsed_ms": int((now - provider_stream_started) * 1000),
                "bridge_total_ms": int((now - started) * 1000),
            }
            chunk_metadata_extra = {}
            if vocal_gesture and vocal_gesture.matched:
                chunk_metadata_extra = {"vocal_gesture_generation": {"matched": True, "reason": vocal_gesture.reason}}
            yield CognitiveChunk(
                text=chunk.text,
                backend=chunk.provider,
                index=chunk.index,
                is_final=chunk.is_final,
                ok=chunk.ok,
                error=chunk.error,
                metadata={
                    **chunk.metadata,
                    **chunk_metadata_extra,
                    "latency_ms": int((perf_counter() - started) * 1000),
                    "bridge": "direct_llm",
                    "bridge_timing": bridge_timing,
                    "context_runtime_state": context.runtime_state,
                },
            )
        if vocal_gesture and vocal_gesture.matched and not emitted_text.strip():
            yield self._fallback_vocal_chunk(text, started=started)
            return
        self._remember_turn(session_id, user=text, assistant=emitted_text)
