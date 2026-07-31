from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .capability_context import CapabilityRequest
from .tool_result import ToolResult


@dataclass(frozen=True)
class CapabilityInfo:
    name: str
    actions: list[str]
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(ABC):
    @abstractmethod
    def info(self) -> CapabilityInfo:
        ...

    @abstractmethod
    def invoke(self, request: CapabilityRequest) -> ToolResult:
        ...
