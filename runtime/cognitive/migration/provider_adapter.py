from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfflineProviderResponse:
    provider: str
    text: str


class OfflineProviderAdapter:
    """Offline provider response adapter for migration tests.

    This adapter never calls network or real LLM providers. It represents already
    captured or synthetic provider responses for deterministic scoring.
    """

    def __init__(self, provider: str, response_text: str):
        self.provider = provider
        self.response_text = response_text

    def run(self) -> OfflineProviderResponse:
        return OfflineProviderResponse(provider=self.provider, text=self.response_text)
