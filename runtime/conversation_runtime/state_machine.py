from __future__ import annotations

from enum import Enum
from typing import Iterable


class ConversationState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    USER_SPEAKING = "user_speaking"
    FINALIZING = "finalizing"
    THINKING = "thinking"
    RESPONDING = "responding"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    ERROR = "error"


_ALLOWED_TRANSITIONS: dict[ConversationState, set[ConversationState]] = {
    ConversationState.IDLE: {ConversationState.LISTENING, ConversationState.ERROR},
    ConversationState.LISTENING: {
        ConversationState.USER_SPEAKING,
        ConversationState.IDLE,
        ConversationState.ERROR,
    },
    ConversationState.USER_SPEAKING: {
        ConversationState.FINALIZING,
        ConversationState.LISTENING,
        ConversationState.ERROR,
    },
    ConversationState.FINALIZING: {
        ConversationState.THINKING,
        ConversationState.LISTENING,
        ConversationState.ERROR,
    },
    ConversationState.THINKING: {ConversationState.RESPONDING, ConversationState.ERROR},
    ConversationState.RESPONDING: {ConversationState.SPEAKING, ConversationState.ERROR},
    ConversationState.SPEAKING: {
        ConversationState.LISTENING,
        ConversationState.INTERRUPTED,
        ConversationState.ERROR,
    },
    ConversationState.INTERRUPTED: {ConversationState.LISTENING, ConversationState.ERROR},
    ConversationState.ERROR: {ConversationState.IDLE, ConversationState.LISTENING},
}


class InvalidStateTransition(ValueError):
    """Raised when a requested conversation state transition is not allowed."""


def allowed_next_states(state: ConversationState) -> tuple[ConversationState, ...]:
    return tuple(_ALLOWED_TRANSITIONS[state])


def can_transition(source: ConversationState, target: ConversationState) -> bool:
    return target in _ALLOWED_TRANSITIONS[source]


class ConversationStateMachine:
    def __init__(self, initial_state: ConversationState = ConversationState.IDLE):
        self.state = initial_state
        self.history: list[ConversationState] = [initial_state]

    def transition_to(self, target: ConversationState) -> ConversationState:
        if not can_transition(self.state, target):
            raise InvalidStateTransition(
                f"invalid conversation transition: {self.state.value} -> {target.value}"
            )
        self.state = target
        self.history.append(target)
        return self.state

    def force_error(self) -> ConversationState:
        self.state = ConversationState.ERROR
        self.history.append(self.state)
        return self.state

    def assert_history(self, expected: Iterable[ConversationState]) -> None:
        actual = tuple(self.history)
        expected_tuple = tuple(expected)
        if actual != expected_tuple:
            raise AssertionError(f"history mismatch: {actual!r} != {expected_tuple!r}")
