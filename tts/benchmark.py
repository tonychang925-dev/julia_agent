from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median
from time import perf_counter
from typing import Any

from .interface import TTSEngine, TTSResult


@dataclass(frozen=True)
class TTSBenchmarkSample:
    index: int
    ok: bool
    engine: str
    text_chars: int
    call_ms: int
    duration_ms: int | None
    audio_path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "ok": self.ok,
            "engine": self.engine,
            "text_chars": self.text_chars,
            "call_ms": self.call_ms,
            "duration_ms": self.duration_ms,
            "audio_path": self.audio_path,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TTSBenchmarkReport:
    samples: list[TTSBenchmarkSample]

    @property
    def count(self) -> int:
        return len(self.samples)

    def summary(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "ok_count": sum(1 for sample in self.samples if sample.ok),
            "engine": self.samples[0].engine if self.samples else None,
            "call_ms": self._stats("call_ms"),
            "duration_ms": self._stats("duration_ms"),
            "text_chars": self._stats("text_chars"),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "samples": [sample.to_dict() for sample in self.samples],
        }

    def _stats(self, key: str) -> dict[str, float | int | None]:
        values = [getattr(sample, key) for sample in self.samples]
        numeric = [int(value) for value in values if isinstance(value, int)]
        if not numeric:
            return {"min": None, "max": None, "mean": None, "median": None}
        return {
            "min": min(numeric),
            "max": max(numeric),
            "mean": round(mean(numeric), 2),
            "median": round(median(numeric), 2),
        }


class TTSBenchmarkRunner:
    """Measures TTS engine call latency for fast-ack startup diagnostics.

    For synchronous engines, call_ms means time until `speak()` returns. For
    dry-run this is near zero; for platform or cloud TTS it approximates startup
    + playback/script completion depending on adapter behavior.
    """

    def __init__(self, engine: TTSEngine):
        self.engine = engine

    def run(self, *, text: str, repeat: int = 3) -> TTSBenchmarkReport:
        samples: list[TTSBenchmarkSample] = []
        for index in range(1, repeat + 1):
            started = perf_counter()
            result = self.engine.speak(text)
            finished = perf_counter()
            call_ms = int((finished - started) * 1000)
            metadata = dict(result.metadata)
            metadata.setdefault("measured_call_ms", call_ms)
            samples.append(self._sample(index=index, result=result, call_ms=call_ms, metadata=metadata))
        return TTSBenchmarkReport(samples=samples)

    @staticmethod
    def _sample(*, index: int, result: TTSResult, call_ms: int, metadata: dict[str, Any]) -> TTSBenchmarkSample:
        return TTSBenchmarkSample(
            index=index,
            ok=result.ok,
            engine=result.engine,
            text_chars=len(result.text),
            call_ms=call_ms,
            duration_ms=result.duration_ms,
            audio_path=result.audio_path,
            error=result.error,
            metadata=metadata,
        )
