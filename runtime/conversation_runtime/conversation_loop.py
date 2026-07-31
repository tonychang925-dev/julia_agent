from __future__ import annotations

from dataclasses import dataclass, field
import re

from audio.ownership import AudioOwner, AudioOwnershipManager
from tts.interface import TTSResult
from tts.chunking import SentenceSegmenter, split_for_tts

from .bridge.cognitive_bridge import CognitiveBridge
from .bridge.echo_adapter import EchoAdapter
from .response_handler import ResponseHandler
from .session import ConversationSession
from .speaking_controller import SpeakingController
from .state_machine import ConversationState
from .turn_manager import ConversationTurn, TurnManager
from .trace import ConversationTrace
from .latency import LatencySnapshot, LatencyTracker
from runtime.cognitive.boundary_detector import BoundaryDetector
from runtime.conversation_archive import TranscriptStore
from runtime.runtime_trace import RuntimeEventStore



_VOICE_TAG_RE = re.compile(r"^\s*(\[(?:呻吟|尖叫|哭|笑|whispers|sighs|sad|excited|nervously|thoughtfully|dramatic|stammers|sarcastically|cheerfully|quietly|gasps|shouts|giggles|laughs|exhales\s+softly|sighs\s+softly|screams\s+softly)\])")


def _extract_voice_tag(text: str) -> str | None:
    match = _VOICE_TAG_RE.match(text or "")
    return match.group(1) if match else None


def _apply_voice_tag_continuity(sentence: str, active_tag: str | None) -> tuple[str, str | None]:
    """Carry the current TTS voice tag across sentence-level streaming chunks.

    ElevenLabs receives each realtime sentence independently. If only the first
    sentence has ``[呻吟]`` and later sentences do not, later audio reverts to
    neutral narration even though the model intended one continuous voice.
    """
    current_tag = _extract_voice_tag(sentence)
    if current_tag:
        return sentence, current_tag
    if active_tag and sentence.strip():
        return f"{active_tag} {sentence.lstrip()}", active_tag
    return sentence, active_tag

@dataclass
class ConversationLoopResult:
    turn: ConversationTurn
    state_history: list[ConversationState]
    event_log: list[str] = field(default_factory=list)
    tts_result: TTSResult | None = None
    trace: ConversationTrace | None = None
    latency: LatencySnapshot | None = None


class ConversationLoop:
    """Local conversation loop for Phase 3.2.3.

    This proves the lifecycle independently from Claude Code:
    FINALIZING -> THINKING -> EchoAdapter -> RESPONDING -> TTS -> SPEAKING -> LISTENING.
    """

    def __init__(
        self,
        session: ConversationSession | None = None,
        bridge: CognitiveBridge | None = None,
        speaking_controller: SpeakingController | None = None,
        audio_owner: AudioOwnershipManager | None = None,
        transcript_store: TranscriptStore | None = None,
        runtime_event_store: RuntimeEventStore | None = None,
    ):
        self.session = session or ConversationSession()
        self.turn_manager = TurnManager(self.session.session_id)
        self.bridge = bridge or EchoAdapter()
        self.response_handler = ResponseHandler(self.bridge)
        self.audio_owner = audio_owner or AudioOwnershipManager()
        self.speaking_controller = speaking_controller or SpeakingController.dry_run(self.audio_owner)
        self.event_log: list[str] = []
        self.last_latency: LatencySnapshot | None = None
        self.boundary_detector = BoundaryDetector()
        self.transcript_store = transcript_store if transcript_store is not None else TranscriptStore.default()
        self.runtime_event_store = runtime_event_store if runtime_event_store is not None else RuntimeEventStore.default()

    def run_text_turn(self, text: str) -> ConversationLoopResult:
        if self.session.state is ConversationState.IDLE:
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")

        self.session.transition_to(ConversationState.USER_SPEAKING)
        self.event_log.append("state=USER_SPEAKING")
        turn = self.turn_manager.start_turn()
        latency_tracker = LatencyTracker()
        latency_tracker.start_turn(turn.turn_id)
        latency_tracker.mark_speech_end()

        self.session.transition_to(ConversationState.FINALIZING)
        self.event_log.append("state=FINALIZING")
        self.turn_manager.finalize_user_text(turn, text)
        latency_tracker.mark_stt_final()
        self.event_log.append(f"text={text}")

        if not text.strip():
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        self.session.transition_to(ConversationState.THINKING)
        self.audio_owner.release()
        self.event_log.append("state=THINKING")
        latency_tracker.mark_bridge_request()
        response = self.response_handler.generate_response(turn)
        latency_tracker.mark_first_chunk()
        if not response.ok:
            self.session.transition_to(ConversationState.ERROR)
            self.event_log.append("state=ERROR")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        self.session.transition_to(ConversationState.RESPONDING)
        self.event_log.append("state=RESPONDING")
        self.event_log.append(f"Cognitive response: {response.text}")
        boundary = self.boundary_detector.detect(response.text, metadata={"backend": response.backend})
        response_metadata = {**response.metadata, "boundary": boundary.to_dict()}
        self.event_log.append(f"boundary={boundary.to_dict()}")
        self.turn_manager.complete_assistant(
            turn,
            text=response.text,
            backend=response.backend,
            metadata=response_metadata,
        )

        self.session.transition_to(ConversationState.SPEAKING)
        self.event_log.append("state=SPEAKING")
        latency_tracker.mark_tts_start()
        tts_result = self.speaking_controller.speak(response.text)
        turn.assistant.tts_result = tts_result
        self.event_log.append(f"[TTS:{tts_result.engine}] {tts_result.text}" if tts_result.ok else f"[TTS_ERROR] {tts_result.error}")

        self.session.transition_to(ConversationState.LISTENING)
        self.audio_owner.acquire(AudioOwner.USER)
        self.event_log.append("state=LISTENING")
        state_history = list(self.session.state_machine.history)
        latency_snapshot = latency_tracker.finish()
        self.last_latency = latency_snapshot
        self.event_log.append(f"latency={latency_snapshot.to_dict()}")
        trace = ConversationTrace.from_turn(
            turn,
            state_history=state_history,
            tts_result=tts_result,
            latency=latency_snapshot.to_dict(),
        )
        if self.transcript_store:
            self.transcript_store.append_trace(trace)
        if self.runtime_event_store:
            self.runtime_event_store.append_trace(trace)
        return ConversationLoopResult(
            turn=turn,
            state_history=state_history,
            event_log=list(self.event_log),
            tts_result=tts_result,
            trace=trace,
            latency=latency_snapshot,
        )

    def run_text_turn_streaming(self, text: str) -> ConversationLoopResult:
        """Phase 3.2.5.1 response streaming loop.

        State semantics stay stable: THINKING waits for bridge stream start,
        RESPONDING records chunks, SPEAKING plays chunks, then returns LISTENING.
        """
        if self.session.state is ConversationState.IDLE:
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")

        self.session.transition_to(ConversationState.USER_SPEAKING)
        self.event_log.append("state=USER_SPEAKING")
        turn = self.turn_manager.start_turn()
        latency_tracker = LatencyTracker()
        latency_tracker.start_turn(turn.turn_id)
        latency_tracker.mark_speech_end()

        self.session.transition_to(ConversationState.FINALIZING)
        self.event_log.append("state=FINALIZING")
        self.turn_manager.finalize_user_text(turn, text)
        latency_tracker.mark_stt_final()
        self.event_log.append(f"text={text}")

        if not text.strip():
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        self.session.transition_to(ConversationState.THINKING)
        self.audio_owner.release()
        self.event_log.append("state=THINKING")
        latency_tracker.mark_bridge_request()
        self.bridge.send_message(text, session_id=self.session.session_id, turn_id=turn.turn_id)

        chunks = []
        backend = ""
        metadata: dict[str, object] = {"streaming": True, "chunks": []}
        for chunk in self.bridge.stream_response(session_id=self.session.session_id, turn_id=turn.turn_id):
            if not chunk.ok:
                self.session.transition_to(ConversationState.ERROR)
                self.event_log.append("state=ERROR")
                return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))
            if not backend:
                backend = chunk.backend
            if self.session.state is ConversationState.THINKING:
                latency_tracker.mark_first_chunk()
                self.session.transition_to(ConversationState.RESPONDING)
                self.event_log.append("state=RESPONDING")
            chunks.append(chunk.text)
            metadata.update({k: v for k, v in chunk.metadata.items() if k not in {"chunks"}})
            metadata["chunks"].append({"index": chunk.index, "text": chunk.text, "is_final": chunk.is_final})  # type: ignore[index]
            self.event_log.append(f"Response chunk[{chunk.index}]: {chunk.text}")

        response_text = "".join(chunks).strip()
        if not response_text:
            self.session.transition_to(ConversationState.ERROR)
            self.event_log.append("state=ERROR")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        boundary = self.boundary_detector.detect(response_text, metadata={"backend": backend or "unknown"})
        metadata["boundary"] = boundary.to_dict()
        self.event_log.append(f"boundary={boundary.to_dict()}")
        self.turn_manager.complete_assistant(
            turn,
            text=response_text,
            backend=backend or "unknown",
            metadata=metadata,
        )

        self.session.transition_to(ConversationState.SPEAKING)
        self.event_log.append("state=SPEAKING")
        latency_tracker.mark_tts_start()
        tts_chunks = split_for_tts(response_text, max_chars=80)
        tts_results = self.speaking_controller.speak_chunks(tts_chunks)
        last_tts_result = tts_results[-1] if tts_results else None
        turn.assistant.tts_result = last_tts_result
        for index, result in enumerate(tts_results):
            self.event_log.append(f"[TTS_CHUNK:{index}:{result.engine}] {result.text}" if result.ok else f"[TTS_CHUNK_ERROR:{index}] {result.error}")

        self.session.transition_to(ConversationState.LISTENING)
        self.audio_owner.acquire(AudioOwner.USER)
        self.event_log.append("state=LISTENING")
        state_history = list(self.session.state_machine.history)
        latency_snapshot = latency_tracker.finish()
        self.last_latency = latency_snapshot
        self.event_log.append(f"latency={latency_snapshot.to_dict()}")
        trace = ConversationTrace.from_turn(
            turn,
            state_history=state_history,
            tts_result=last_tts_result,
            latency=latency_snapshot.to_dict(),
        )
        if self.transcript_store:
            self.transcript_store.append_trace(trace)
        if self.runtime_event_store:
            self.runtime_event_store.append_trace(trace)
        return ConversationLoopResult(
            turn=turn,
            state_history=state_history,
            event_log=list(self.event_log),
            tts_result=last_tts_result,
            trace=trace,
            latency=latency_snapshot,
        )

    def run_text_turn_realtime_speech(self, text: str, *, fast_ack_text: str | None = None) -> ConversationLoopResult:
        """Phase 3.2.5.3 sentence-level realtime speech output.

        Cognitive chunks are incrementally segmented into complete sentences. The
        first complete sentence starts TTS immediately instead of waiting for the
        full assistant response.
        """
        if self.session.state is ConversationState.IDLE:
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")

        self.session.transition_to(ConversationState.USER_SPEAKING)
        self.event_log.append("state=USER_SPEAKING")
        turn = self.turn_manager.start_turn()
        latency_tracker = LatencyTracker()
        latency_tracker.start_turn(turn.turn_id)
        latency_tracker.mark_speech_end()

        self.session.transition_to(ConversationState.FINALIZING)
        self.event_log.append("state=FINALIZING")
        self.turn_manager.finalize_user_text(turn, text)
        latency_tracker.mark_stt_final()
        self.event_log.append(f"text={text}")

        if not text.strip():
            self.session.transition_to(ConversationState.LISTENING)
            self.audio_owner.acquire(AudioOwner.USER)
            self.event_log.append("state=LISTENING")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        self.session.transition_to(ConversationState.THINKING)
        self.audio_owner.release()
        self.event_log.append("state=THINKING")
        latency_tracker.mark_bridge_request()
        self.bridge.send_message(text, session_id=self.session.session_id, turn_id=turn.turn_id)

        segmenter = SentenceSegmenter(max_chars=60)
        response_parts: list[str] = []
        tts_results: list[TTSResult] = []
        backend = ""
        metadata: dict[str, object] = {"streaming": True, "realtime_speech": True, "chunks": [], "spoken_sentences": []}
        queue = None
        player = None
        active_voice_tag: str | None = None

        if fast_ack_text:
            latency_tracker.mark_tts_start()
            ack_result = self.speaking_controller.speak(fast_ack_text)
            metadata["fast_ack"] = {
                "text": fast_ack_text,
                "tts_engine": ack_result.engine,
                "ok": ack_result.ok,
                "duration_ms": ack_result.duration_ms,
            }
            self.event_log.append(
                f"[TTS_ACK:{ack_result.engine}] {ack_result.text}" if ack_result.ok else f"[TTS_ACK_ERROR] {ack_result.error}"
            )

        def play_sentence(sentence: str) -> None:
            nonlocal queue, player, active_voice_tag
            sentence, active_voice_tag = _apply_voice_tag_continuity(sentence, active_voice_tag)
            if self.session.state is ConversationState.RESPONDING:
                self.session.transition_to(ConversationState.SPEAKING)
                self.event_log.append("state=SPEAKING")
                latency_tracker.mark_tts_start()
                queue, player = self.speaking_controller.start_realtime_output()
            if queue is None or player is None:
                queue, player = self.speaking_controller.start_realtime_output()
            result = self.speaking_controller.play_realtime_sentence(queue, player, sentence)
            if result is not None:
                tts_results.append(result)
                metadata["spoken_sentences"].append(sentence)  # type: ignore[index]
                self.event_log.append(f"[TTS_SENTENCE:{len(tts_results)-1}:{result.engine}] {result.text}" if result.ok else f"[TTS_SENTENCE_ERROR:{len(tts_results)-1}] {result.error}")

        for chunk in self.bridge.stream_response(session_id=self.session.session_id, turn_id=turn.turn_id):
            if not chunk.ok:
                if queue is not None:
                    self.speaking_controller.clear_realtime_output(queue)
                self.session.transition_to(ConversationState.ERROR)
                self.event_log.append("state=ERROR")
                if chunk.error:
                    self.event_log.append(f"[BRIDGE_ERROR] {chunk.error}")
                return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))
            if not backend:
                backend = chunk.backend
            if self.session.state is ConversationState.THINKING:
                latency_tracker.mark_first_chunk()
                self.session.transition_to(ConversationState.RESPONDING)
                self.event_log.append("state=RESPONDING")
            response_parts.append(chunk.text)
            metadata.update({k: v for k, v in chunk.metadata.items() if k not in {"chunks"}})
            metadata["chunks"].append({"index": chunk.index, "text": chunk.text, "is_final": chunk.is_final})  # type: ignore[index]
            self.event_log.append(f"Response chunk[{chunk.index}]: {chunk.text}")
            for sentence in segmenter.push(chunk.text):
                self.event_log.append(f"Sentence segment: {sentence}")
                play_sentence(sentence)

        for sentence in segmenter.flush():
            if self.session.state is ConversationState.THINKING:
                self.session.transition_to(ConversationState.RESPONDING)
                self.event_log.append("state=RESPONDING")
                latency_tracker.mark_first_chunk()
            self.event_log.append(f"Sentence segment: {sentence}")
            play_sentence(sentence)

        if queue is not None and player is not None:
            extra_results = self.speaking_controller.finish_realtime_output(queue, player)
            tts_results.extend(extra_results)

        response_text = "".join(response_parts).strip()
        if not response_text:
            self.session.transition_to(ConversationState.ERROR)
            self.event_log.append("state=ERROR")
            return ConversationLoopResult(turn=turn, state_history=list(self.session.state_machine.history), event_log=list(self.event_log))

        boundary = self.boundary_detector.detect(response_text, metadata={"backend": backend or "unknown"})
        metadata["boundary"] = boundary.to_dict()
        self.event_log.append(f"boundary={boundary.to_dict()}")

        last_tts_result = tts_results[-1] if tts_results else None
        self.turn_manager.complete_assistant(
            turn,
            text=response_text,
            backend=backend or "unknown",
            metadata=metadata,
        )
        turn.assistant.tts_result = last_tts_result

        if self.session.state is ConversationState.RESPONDING:
            self.session.transition_to(ConversationState.SPEAKING)
            self.event_log.append("state=SPEAKING")
            latency_tracker.mark_tts_start()

        self.session.transition_to(ConversationState.LISTENING)
        self.audio_owner.acquire(AudioOwner.USER)
        self.event_log.append("state=LISTENING")
        state_history = list(self.session.state_machine.history)
        latency_snapshot = latency_tracker.finish()
        self.last_latency = latency_snapshot
        self.event_log.append(f"latency={latency_snapshot.to_dict()}")
        trace = ConversationTrace.from_turn(
            turn,
            state_history=state_history,
            tts_result=last_tts_result,
            latency=latency_snapshot.to_dict(),
        )
        if self.transcript_store:
            self.transcript_store.append_trace(trace)
        if self.runtime_event_store:
            self.runtime_event_store.append_trace(trace)
        return ConversationLoopResult(
            turn=turn,
            state_history=state_history,
            event_log=list(self.event_log),
            tts_result=last_tts_result,
            trace=trace,
            latency=latency_snapshot,
        )
