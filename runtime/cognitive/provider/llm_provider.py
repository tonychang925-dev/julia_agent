from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from runtime.cognitive.cognitive_context import JuliaContext
from runtime.cognitive.provider.capability import ProviderInfo


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    ok: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMChunk:
    text: str
    provider: str
    index: int
    is_final: bool = False
    ok: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    def info(self) -> ProviderInfo:
        return ProviderInfo(name=self.__class__.__name__, model="unknown", supports_stream=True)

    @abstractmethod
    def generate(self, context: JuliaContext) -> LLMResponse:
        ...

    def stream(self, context: JuliaContext) -> Iterator[LLMChunk]:
        response = self.generate(context)
        yield LLMChunk(
            text=response.text,
            provider=response.provider,
            index=0,
            is_final=True,
            ok=response.ok,
            error=response.error,
            metadata=response.metadata,
        )
