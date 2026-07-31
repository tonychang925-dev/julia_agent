from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class LatencySnapshot:
    turn_id: int
    latency: dict[str, int | None]
    targets: dict[str, int]
    passed: dict[str, bool | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "latency": self.latency,
            "targets": self.targets,
            "passed": self.passed,
        }


class LatencyTracker:
    """Tracks per-turn realtime conversation latency.

    Primary user-facing metric: Time To First Voice (TTFV), from speech end / STT
    finalization to first TTS chunk start.
    """

    DEFAULT_TARGETS_MS = {
        "speech_to_text_ms": 500,
        "bridge_first_chunk_ms": 1500,
        "tts_start_ms": 500,
        "time_to_first_voice_ms": 2500,
    }

    def __init__(self, targets_ms: dict[str, int] | None = None):
        self.targets_ms = dict(self.DEFAULT_TARGETS_MS)
        if targets_ms:
            self.targets_ms.update(targets_ms)
        self.turn_id: int | None = None
        self._marks: dict[str, float] = {}

    def start_turn(self, turn_id: int) -> None:
        self.turn_id = turn_id
        self._marks = {"turn_start": perf_counter()}

    def mark_speech_end(self) -> None:
        self._marks["speech_end"] = perf_counter()

    def mark_stt_final(self) -> None:
        self._marks["stt_final"] = perf_counter()

    def mark_bridge_request(self) -> None:
        self._marks["bridge_request"] = perf_counter()

    def mark_first_chunk(self) -> None:
        self._marks.setdefault("first_chunk", perf_counter())

    def mark_tts_start(self) -> None:
        self._marks.setdefault("tts_start", perf_counter())

    def finish(self) -> LatencySnapshot:
        self._marks["turn_finished"] = perf_counter()
        latency = {
            "speech_to_text_ms": self._delta_ms("speech_end", "stt_final"),
            "bridge_first_chunk_ms": self._delta_ms("bridge_request", "first_chunk"),
            "tts_start_ms": self._delta_ms("first_chunk", "tts_start"),
            "time_to_first_voice_ms": self._delta_ms("speech_end", "tts_start"),
            "total_response_ms": self._delta_ms("speech_end", "turn_finished"),
        }
        passed = {
            key: None if latency.get(key) is None else latency[key] <= target
            for key, target in self.targets_ms.items()
        }
        return LatencySnapshot(
            turn_id=self.turn_id or 0,
            latency=latency,
            targets=self.targets_ms,
            passed=passed,
        )

    def _delta_ms(self, start_key: str, end_key: str) -> int | None:
        if start_key not in self._marks or end_key not in self._marks:
            return None
        return max(0, int((self._marks[end_key] - self._marks[start_key]) * 1000))
