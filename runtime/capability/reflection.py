from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability_context import CapabilityRequest
from .tool_result import ToolResult


@dataclass(frozen=True)
class ToolReflection:
    event: str
    capability: str
    action: str
    ok: bool
    output: str
    error: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "capability": self.capability,
            "action": self.action,
            "ok": self.ok,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class ToolReflectionBuilder:
    def build(self, request: CapabilityRequest, result: ToolResult) -> ToolReflection:
        return ToolReflection(
            event="tool_execution_result",
            capability=request.capability,
            action=request.action,
            ok=result.ok,
            output=result.output,
            error=result.error,
            metadata={"request": request.to_dict(), "tool_result": result.to_dict()},
        )
