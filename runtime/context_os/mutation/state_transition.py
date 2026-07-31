from __future__ import annotations

from dataclasses import dataclass

from runtime.context_os.execution.context_mutation import MutationType

from .context_state import ContextWorkingState, OpenLoopState
from .mutation_decision import MutationDecision
from .open_loop_tracker import OpenLoopTracker


@dataclass
class StateTransitionEngine:
    open_loop_tracker: OpenLoopTracker

    def apply(self, *, state: ContextWorkingState, decisions: list[MutationDecision]) -> ContextWorkingState:
        next_state = state
        for decision in decisions:
            if not decision.accepted:
                continue
            event = decision.event
            if event.mutation_type == MutationType.CURRENT_ARC_UPDATE and event.value:
                next_state = next_state.with_updates(current_arc=event.value)
            elif event.mutation_type == MutationType.TASK_PROGRESS_UPDATE and event.value:
                next_state = next_state.with_updates(current_task=event.value)
            elif event.mutation_type == MutationType.COGNITIVE_MODE_CHANGED and event.value:
                history = [*next_state.mode_transition_history, event.value]
                next_state = next_state.with_updates(cognitive_mode=event.value, mode_transition_history=history)
            elif event.mutation_type == MutationType.OPEN_LOOP_CREATED and event.value:
                loop = OpenLoopState(loop_id=f"open_loop_{abs(hash((event.source_turn_id, event.value))) % 10**10}", title=event.value, source_turn_id=event.source_turn_id)
                loops = [*next_state.open_loops]
                if not any(existing.title == loop.title and existing.status == "open" for existing in loops):
                    loops.append(loop)
                next_state = next_state.with_updates(open_loops=loops)
            elif event.mutation_type == MutationType.OPEN_LOOP_RESOLVED:
                loops = self.open_loop_tracker.resolve_loops(text=event.value or event.reason, loops=next_state.open_loops)
                next_state = next_state.with_updates(open_loops=loops)
            elif event.mutation_type == MutationType.EVIDENCE_GAP_FOUND:
                gaps = [*next_state.evidence_gaps, {"turn_id": event.source_turn_id, "reason": event.reason, "target": event.target, **event.metadata}]
                next_state = next_state.with_updates(evidence_gaps=gaps)
            elif event.mutation_type == MutationType.QUALITY_WARNING:
                warnings = [*next_state.quality_warnings, event.reason]
                next_state = next_state.with_updates(quality_warnings=warnings)
        return next_state
