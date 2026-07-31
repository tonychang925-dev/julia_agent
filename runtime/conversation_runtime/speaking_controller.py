from __future__ import annotations

from dataclasses import dataclass

from audio.ownership import AudioOwner, AudioOwnershipManager
from tts.interface import TTSEngine, TTSResult
from tts.player import AudioPlayer
from tts.queue import TTSQueue
from tts.local_tts import LocalTTSEngine


@dataclass
class SpeakingController:
    tts_engine: TTSEngine
    audio_owner: AudioOwnershipManager

    @classmethod
    def dry_run(cls, audio_owner: AudioOwnershipManager | None = None) -> "SpeakingController":
        return cls(tts_engine=LocalTTSEngine(mode="dry_run"), audio_owner=audio_owner or AudioOwnershipManager())

    def speak(self, text: str) -> TTSResult:
        self.audio_owner.release()
        self.audio_owner.acquire(AudioOwner.TTS)
        try:
            return self.tts_engine.speak(text)
        finally:
            self.audio_owner.release()

    def speak_chunks(self, chunks: list[str]) -> list[TTSResult]:
        self.audio_owner.release()
        self.audio_owner.acquire(AudioOwner.TTS)
        results: list[TTSResult] = []
        try:
            for chunk in chunks:
                results.append(self.tts_engine.speak(chunk))
            return results
        finally:
            self.audio_owner.release()

    def start_realtime_output(self) -> tuple[TTSQueue, AudioPlayer]:
        self.audio_owner.release()
        self.audio_owner.acquire(AudioOwner.TTS)
        return TTSQueue(), AudioPlayer(self.tts_engine)

    def play_realtime_sentence(self, queue: TTSQueue, player: AudioPlayer, sentence: str) -> TTSResult | None:
        queue.enqueue(sentence)
        return player.play_next(queue)

    def finish_realtime_output(self, queue: TTSQueue, player: AudioPlayer) -> list[TTSResult]:
        try:
            return player.drain(queue)
        finally:
            self.audio_owner.release()

    def clear_realtime_output(self, queue: TTSQueue) -> None:
        queue.clear()
        self.audio_owner.release()
