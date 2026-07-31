from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TTSResult:
    ok: bool
    text: str
    engine: str
    duration_ms: int | None = None
    audio_path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TTSEngine(ABC):
    @abstractmethod
    def speak(self, text: str) -> TTSResult:
        ...
