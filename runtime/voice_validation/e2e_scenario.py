from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VoiceE2EScenario:
    scenario_id: str
    input_text: str
    expected_persona: str = "Julia"
    expected_user: str = "Tony"
    expected_mode: str | None = None
    expected_memory_topics: list[str] = field(default_factory=list)
    latency_target_ms: int = 2500
