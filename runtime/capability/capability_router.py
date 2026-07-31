from __future__ import annotations

from dataclasses import dataclass, field

from .capability_context import CapabilityRequest
from .capability_provider import CapabilityInfo, CapabilityProvider
from .tool_result import ToolResult


@dataclass
class CapabilityRouter:
    providers: dict[str, CapabilityProvider] = field(default_factory=dict)

    def register(self, provider: CapabilityProvider) -> None:
        self.providers[provider.info().name] = provider

    def list_capabilities(self) -> list[CapabilityInfo]:
        return [provider.info() for provider in self.providers.values()]

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        provider = self.providers.get(request.capability)
        if provider is None:
            return ToolResult(
                ok=False,
                tool=request.capability,
                error=f"capability not registered: {request.capability}",
                metadata={"action": request.action},
            )
        return provider.invoke(request)
