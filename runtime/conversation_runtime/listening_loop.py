from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from audio.buffer import AudioFrame
from audio.ownership import AudioOwner, AudioOwnershipManager
from audio.vad_engine import VADEngine, VADEventType
from stt.finalizer import MockSTTFinalizer, STTResult

from .session import ConversationSession
from .state_machine import ConversationState


@dataclass
class ListeningLoopResult:
    finalized_texts: list[str]
    state_history: list[ConversationState]
    event_log: list[str]


class ContinuousListeningLoop:
    """Phase 3.2.2 dependency-free listening loop over supplied AudioFrame objects."""

    def __init__(
        self,
        session: ConversationSession | None = None,
        vad: VADEngine | None = None,
        stt_finalizer: MockSTTFinalizer | None = None,
        audio_owner: AudioOwnershipManager | None = None,
    ):
        self.session = session or ConversationSession()
        self.vad = vad or VADEngine()
        self.stt_finalizer = stt_finalizer or MockSTTFinalizer()
        self.audio_owner = audio_owner or AudioOwnershipManager()
        self.finalized_texts: list[str] = []
        self.event_log: list[str] = []

    def run_frames(self, frames: Iterable[AudioFrame]) -> ListeningLoopResult:
        if self.session.state is ConversationState.IDLE:
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("Julia Voice Runtime started")
            self.event_log.append("state=LISTENING")

        for frame in frames:
            event = self.vad.process_frame(frame)
            if event.type is VADEventType.SPEECH_STARTED:
                self.session.transition_to(ConversationState.USER_SPEAKING)
                self.event_log.append("state=USER_SPEAKING")
            elif event.type is VADEventType.SPEECH_FINALIZED and event.segment is not None:
                self.session.transition_to(ConversationState.FINALIZING)
                self.event_log.append("finalizing...")
                stt_result = self.stt_finalizer.finalize(event.segment)
                self._handle_stt_result(stt_result)
                self.session.transition_to(ConversationState.LISTENING)
                self.event_log.append("state=LISTENING")
            elif event.type is VADEventType.SPEECH_DISCARDED:
                self.session.transition_to(ConversationState.LISTENING)
                self.event_log.append(f"discarded_segment reason={event.reason}")
                self.event_log.append("state=LISTENING")

        return ListeningLoopResult(
            finalized_texts=list(self.finalized_texts),
            state_history=list(self.session.state_machine.history),
            event_log=list(self.event_log),
        )

    def _handle_stt_result(self, result: STTResult) -> None:
        if result.ok and result.text.strip():
            self.finalized_texts.append(result.text)
            self.event_log.append("text:")
            self.event_log.append(result.text)
