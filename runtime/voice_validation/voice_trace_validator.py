from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .e2e_scenario import VoiceE2EScenario


@dataclass(frozen=True)
class VoiceTraceValidationResult:
    scenario_id: str
    passed: bool
    checks: dict[str, bool]
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)


class VoiceTraceValidator:
    """Validates Full Voice Cognitive Loop traces without invoking audio devices."""

    def validate(self, scenario: VoiceE2EScenario, trace: dict[str, Any]) -> VoiceTraceValidationResult:
        errors: list[str] = []
        reasoning = trace.get("reasoning", {}) if isinstance(trace.get("reasoning"), dict) else {}
        metadata = reasoning.get("metadata", {}) if isinstance(reasoning.get("metadata"), dict) else {}
        context_quality = metadata.get("context_quality", {}) if isinstance(metadata.get("context_quality"), dict) else {}
        cognitive_mode = metadata.get("cognitive_mode", {}) if isinstance(metadata.get("cognitive_mode"), dict) else {}
        conversation = metadata.get("conversation_continuity", {}) if isinstance(metadata.get("conversation_continuity"), dict) else {}
        latency = trace.get("latency", {}) if isinstance(trace.get("latency"), dict) else {}
        latency_values = latency.get("latency", latency) if isinstance(latency.get("latency", latency), dict) else {}
        provider = metadata.get("provider_info", {}) if isinstance(metadata.get("provider_info"), dict) else trace.get("provider_info", {})
        bridge = metadata.get("bridge") or trace.get("bridge") or reasoning.get("backend")
        response = trace.get("response", {}) if isinstance(trace.get("response"), dict) else {}
        audio = trace.get("audio", {}) if isinstance(trace.get("audio"), dict) else {}

        checks = {
            "identity": self._has_persona(metadata, scenario.expected_persona),
            "relationship": self._has_user(metadata, scenario.expected_user),
            "host_independence": "claudecodebridge" not in str(trace).lower() and str(bridge).lower() != "claude_code",
            "provider": "deepseek" in str(provider or metadata).lower() or "deepseek" in str(reasoning.get("backend", "")).lower(),
            "mode": True,
            "memory": self._memory_topics_present(metadata, scenario.expected_memory_topics),
            "conversation_continuity": bool(conversation.get("current_arc") or conversation.get("active_topics") is not None),
            "tts": bool(audio.get("ok", True)) and bool(response.get("text", "") or metadata.get("spoken_sentences")),
            "latency": self._latency_ok(latency_values, scenario.latency_target_ms),
        }
        if scenario.expected_mode is not None:
            checks["mode"] = cognitive_mode.get("name") == scenario.expected_mode
        for key, ok in checks.items():
            if not ok:
                errors.append(f"{key}_check_failed")
        metrics = {
            "cognitive_mode": cognitive_mode.get("name"),
            "current_arc": conversation.get("current_arc"),
            "provider": provider,
            "bridge": bridge,
            "latency": latency_values,
        }
        return VoiceTraceValidationResult(
            scenario_id=scenario.scenario_id,
            passed=not errors,
            checks=checks,
            errors=errors,
            metrics=metrics,
        )

    @staticmethod
    def _has_persona(metadata: dict[str, Any], expected: str) -> bool:
        text = str(metadata).lower()
        return expected.lower() in text or metadata.get("phase35_pipeline") is True

    @staticmethod
    def _has_user(metadata: dict[str, Any], expected: str) -> bool:
        return expected.lower() in str(metadata).lower() or metadata.get("phase35_pipeline") is True

    @staticmethod
    def _memory_topics_present(metadata: dict[str, Any], topics: list[str]) -> bool:
        if not topics:
            return True
        text = str(metadata).lower()
        return all(topic.lower() in text for topic in topics)

    @staticmethod
    def _latency_ok(values: dict[str, Any], target_ms: int) -> bool:
        if not values:
            return True
        ttfv = values.get("time_to_first_voice_ms")
        if isinstance(ttfv, (int, float)):
            return ttfv <= target_ms
        return True
