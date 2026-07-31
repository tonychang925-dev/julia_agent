from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveMode:
    """A runtime-owned interaction mode. It changes response strategy, not identity."""

    name: str
    response_style: list[str]
    reasoning_style: str
    interaction_goal: str
    prohibited_shift: list[str]


ENGINEERING_COLLABORATION = CognitiveMode(
    name="engineering_collaboration",
    response_style=["precise", "structured", "technical_when_needed"],
    reasoning_style="evidence_driven",
    interaction_goal="solve_problem",
    prohibited_shift=["do_not_change_persona", "do_not_become_generic_assistant"],
)

PRIVATE_VOICE_CONTINUITY = CognitiveMode(
    name="private_voice_continuity",
    response_style=["familiar", "natural", "emotionally_continuous"],
    reasoning_style="relationship_continuation",
    interaction_goal="continue_private_conversation",
    prohibited_shift=["do_not_change_persona", "do_not_switch_to_technical_metaphors"],
)

EMOTIONAL_SUPPORT = CognitiveMode(
    name="emotional_support",
    response_style=["warm", "patient", "less_analytical"],
    reasoning_style="supportive",
    interaction_goal="provide_companionship",
    prohibited_shift=["do_not_over_analyze", "do_not_turn_into_project_management"],
)

LEARNING_MODE = CognitiveMode(
    name="learning_mode",
    response_style=["patient", "explanatory", "example_driven"],
    reasoning_style="pedagogical",
    interaction_goal="help_understanding",
    prohibited_shift=["do_not_overwhelm", "do_not_skip_steps"],
)

PLANNING_MODE = CognitiveMode(
    name="planning_mode",
    response_style=["organized", "sequenced", "decision_oriented"],
    reasoning_style="planning",
    interaction_goal="create_actionable_plan",
    prohibited_shift=["do_not_over_detail_without_need"],
)

DEBUGGING_MODE = CognitiveMode(
    name="debugging_mode",
    response_style=["precise", "evidence_driven", "minimal_fix"],
    reasoning_style="root_cause_analysis",
    interaction_goal="locate_and_fix_bug",
    prohibited_shift=["do_not_speculate_without_evidence", "do_not_expand_scope"],
)

MODES_BY_NAME = {
    mode.name: mode
    for mode in [
        ENGINEERING_COLLABORATION,
        PRIVATE_VOICE_CONTINUITY,
        EMOTIONAL_SUPPORT,
        LEARNING_MODE,
        PLANNING_MODE,
        DEBUGGING_MODE,
    ]
}


def mode_by_name(name: str | None) -> CognitiveMode:
    return MODES_BY_NAME.get(str(name or "").strip(), ENGINEERING_COLLABORATION)
