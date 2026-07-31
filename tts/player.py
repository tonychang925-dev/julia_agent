from __future__ import annotations

from dataclasses import dataclass, field

from .interface import TTSEngine, TTSResult
from .queue import TTSQueue


@dataclass
class AudioPlayer:
    """Synchronous queue player for Phase 3.2.5.3.

    Future implementations can make this async and interruptible without changing
    TTSQueue or Conversation Runtime contracts.
    """

    tts_engine: TTSEngine
    played_results: list[TTSResult] = field(default_factory=list)

    def play_next(self, queue: TTSQueue) -> TTSResult | None:
        sentence = queue.play_next()
        if sentence is None:
            return None
        result = self.tts_engine.speak(sentence)
        self.played_results.append(result)
        return result

    def drain(self, queue: TTSQueue) -> list[TTSResult]:
        results: list[TTSResult] = []
        while len(queue):
            result = self.play_next(queue)
            if result is not None:
                results.append(result)
        return results
