from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any

from .conversation_loop import ConversationLoop, ConversationLoopResult


@dataclass(frozen=True)
class LatencyBenchmarkSample:
    index: int
    ok: bool
    text: str
    backend: str
    boundary_detected: bool
    prompt_input_chars: int | None
    context_build_ms: int | None
    prompt_build_ms: int | None
    http_response_open_ms: int | None
    provider_first_token_ms: int | None
    tts_start_ms: int | None
    time_to_first_voice_ms: int | None
    total_response_ms: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "ok": self.ok,
            "text": self.text,
            "backend": self.backend,
            "boundary_detected": self.boundary_detected,
            "prompt_input_chars": self.prompt_input_chars,
            "context_build_ms": self.context_build_ms,
            "prompt_build_ms": self.prompt_build_ms,
            "http_response_open_ms": self.http_response_open_ms,
            "provider_first_token_ms": self.provider_first_token_ms,
            "tts_start_ms": self.tts_start_ms,
            "time_to_first_voice_ms": self.time_to_first_voice_ms,
            "total_response_ms": self.total_response_ms,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class LatencyBenchmarkReport:
    samples: list[LatencyBenchmarkSample]

    @property
    def count(self) -> int:
        return len(self.samples)

    def summary(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "boundary_count": sum(1 for sample in self.samples if sample.boundary_detected),
            "prompt_input_chars": self._stats("prompt_input_chars"),
            "provider_first_token_ms": self._stats("provider_first_token_ms"),
            "http_response_open_ms": self._stats("http_response_open_ms"),
            "tts_start_ms": self._stats("tts_start_ms"),
            "time_to_first_voice_ms": self._stats("time_to_first_voice_ms"),
            "total_response_ms": self._stats("total_response_ms"),
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


class LatencyBenchmarkRunner:
    def __init__(self, loop_factory):
        self.loop_factory = loop_factory

    def run(
        self,
        *,
        text: str,
        repeat: int = 3,
        realtime_speech: bool = True,
        stream: bool = True,
        fast_ack_text: str | None = None,
    ) -> LatencyBenchmarkReport:
        samples: list[LatencyBenchmarkSample] = []
        for index in range(1, repeat + 1):
            loop: ConversationLoop = self.loop_factory()
            if realtime_speech:
                result = loop.run_text_turn_realtime_speech(text, fast_ack_text=fast_ack_text)
            elif stream:
                result = loop.run_text_turn_streaming(text)
            else:
                result = loop.run_text_turn(text)
            samples.append(self._sample_from_result(index=index, text=text, result=result))
        return LatencyBenchmarkReport(samples=samples)

    @staticmethod
    def _sample_from_result(*, index: int, text: str, result: ConversationLoopResult) -> LatencyBenchmarkSample:
        trace = result.trace.to_dict() if result.trace else {}
        reasoning = trace.get("reasoning", {}) if isinstance(trace, dict) else {}
        metadata = reasoning.get("metadata", {}) if isinstance(reasoning, dict) else {}
        latency = trace.get("latency", {}).get("latency", {}) if isinstance(trace, dict) else {}
        provider_timing = metadata.get("provider_timing", {}) if isinstance(metadata, dict) else {}
        bridge_timing = metadata.get("bridge_timing", {}) if isinstance(metadata, dict) else {}
        boundary = metadata.get("boundary", {}) if isinstance(metadata, dict) else {}
        return LatencyBenchmarkSample(
            index=index,
            ok=bool(result.turn.assistant.text),
            text=text,
            backend=str(reasoning.get("backend") or result.turn.assistant.cognitive_backend or "unknown"),
            boundary_detected=bool(boundary.get("boundary_detected")) if isinstance(boundary, dict) else False,
            prompt_input_chars=_int_or_none(provider_timing.get("prompt_input_chars")),
            context_build_ms=_int_or_none(bridge_timing.get("context_build_ms")),
            prompt_build_ms=_int_or_none(provider_timing.get("prompt_build_ms")),
            http_response_open_ms=_int_or_none(provider_timing.get("http_response_open_ms")),
            provider_first_token_ms=_int_or_none(provider_timing.get("provider_first_token_ms")),
            tts_start_ms=_int_or_none(latency.get("tts_start_ms")),
            time_to_first_voice_ms=_int_or_none(latency.get("time_to_first_voice_ms")),
            total_response_ms=_int_or_none(latency.get("total_response_ms")),
            metadata={"provider": metadata.get("provider"), "model": metadata.get("model")},
        )


def _int_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None
