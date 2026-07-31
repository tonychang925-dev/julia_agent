from __future__ import annotations

from dataclasses import dataclass, field

from runtime.context_os.execution.context_turn import ContextTurn
from runtime.context_os.execution.context_mutation import MutationType
from runtime.context_os.planner.context_intent import ContextIntentType

from .arc_tracker import CurrentArcTracker
from .context_state import ContextWorkingState
from .mutation_decision import MutationDecision
from .mutation_event import ContextMutationEvent
from .mutation_policy import MutationPolicy
from .open_loop_tracker import OpenLoopTracker
from .state_transition import StateTransitionEngine
from .task_progress_tracker import TaskProgressTracker


@dataclass(frozen=True)
class MutationRuntimeResult:
    events: list[ContextMutationEvent]
    decisions: list[MutationDecision]
    previous_state: ContextWorkingState
    next_state: ContextWorkingState


@dataclass
class ContextMutationRuntime:
    arc_tracker: CurrentArcTracker = field(default_factory=CurrentArcTracker)
    open_loop_tracker: OpenLoopTracker = field(default_factory=OpenLoopTracker)
    task_tracker: TaskProgressTracker = field(default_factory=TaskProgressTracker)
    policy: MutationPolicy = field(default_factory=MutationPolicy)

    def process_turn(self, *, state: ContextWorkingState, turn: ContextTurn) -> MutationRuntimeResult:
        events = self.detect_events(turn=turn)
        decisions = [self.policy.decide(state=state, event=event) for event in events]
        next_state = StateTransitionEngine(self.open_loop_tracker).apply(state=state, decisions=decisions)
        return MutationRuntimeResult(events=events, decisions=decisions, previous_state=state, next_state=next_state)

    def detect_events(self, *, turn: ContextTurn) -> list[ContextMutationEvent]:
        text = f"{turn.user_input}\n{turn.response or ''}"
        evidence_refs = [eid for block in turn.selected_blocks for eid in block.evidence_ids]
        events: list[ContextMutationEvent] = []
        arc = self.arc_tracker.infer_arc(text)
        if arc:
            events.append(ContextMutationEvent.create(
                MutationType.CURRENT_ARC_UPDATE,
                source_turn_id=turn.turn_id,
                reason=f"Inferred current arc from turn text: {arc}",
                value=arc,
                target="current_arc",
                evidence_refs=evidence_refs,
                confidence=0.78,
            ))
        task = self.task_tracker.infer_task(text)
        if task or turn.context_plan.intent_type in {ContextIntentType.PLANNING, ContextIntentType.TECHNICAL_DEBUG, ContextIntentType.CURRENT_TASK_QUESTION}:
            events.append(ContextMutationEvent.create(
                MutationType.TASK_PROGRESS_UPDATE,
                source_turn_id=turn.turn_id,
                reason="Turn indicates task progress or planning intent.",
                value=task or turn.context_plan.intent_type.value,
                target="current_task",
                evidence_refs=evidence_refs,
                confidence=0.74,
            ))
        loop = self.open_loop_tracker.create_loop(text=turn.user_input, source_turn_id=turn.turn_id)
        if loop:
            events.append(ContextMutationEvent.create(
                MutationType.OPEN_LOOP_CREATED,
                source_turn_id=turn.turn_id,
                reason="User input created/refreshed an actionable open loop.",
                value=loop.title,
                target="open_loop",
                confidence=0.72,
            ))
        if any(marker in text for marker in ["完成", "已完成", "解决", "分析完成"]):
            events.append(ContextMutationEvent.create(
                MutationType.OPEN_LOOP_RESOLVED,
                source_turn_id=turn.turn_id,
                reason="Turn indicates a previous open loop may be resolved.",
                value=text,
                target="open_loop",
                confidence=0.7,
            ))
        mode = self._mode_from_turn(turn)
        if mode:
            events.append(ContextMutationEvent.create(
                MutationType.COGNITIVE_MODE_CHANGED,
                source_turn_id=turn.turn_id,
                reason=f"Context plan indicates cognitive mode shift to {mode}.",
                value=mode,
                target="cognitive_mode",
                confidence=0.76,
            ))
        if turn.quality and turn.quality.evidence_count == 0 and turn.quality.hallucination_risk >= 0.6:
            events.append(ContextMutationEvent.create(
                MutationType.EVIDENCE_GAP_FOUND,
                source_turn_id=turn.turn_id,
                reason="Quality evaluator detected high hallucination risk with no evidence.",
                target="evidence",
                value="missing",
                confidence=0.9,
                metadata={"hallucination_risk": turn.quality.hallucination_risk},
            ))
        if turn.quality:
            for warning in turn.quality.warnings:
                events.append(ContextMutationEvent.create(
                    MutationType.QUALITY_WARNING,
                    source_turn_id=turn.turn_id,
                    reason=warning,
                    target="context_quality",
                    confidence=0.85,
                ))
        return events

    @staticmethod
    def _mode_from_turn(turn: ContextTurn) -> str | None:
        if turn.context_plan.intent_type == ContextIntentType.EMOTIONAL_SUPPORT:
            return "emotional_support"
        if turn.context_plan.intent_type == ContextIntentType.PRIVATE_VOICE_CONTINUITY:
            return "private_voice_continuity"
        if turn.context_plan.intent_type in {ContextIntentType.PLANNING, ContextIntentType.TECHNICAL_DEBUG, ContextIntentType.CURRENT_TASK_QUESTION}:
            return "engineering_collaboration"
        return None
