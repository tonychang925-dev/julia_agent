from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderAdaptationProfile:
    """Provider-specific expression guidance inside Julia's Runtime boundary.

    This profile adapts wording and fallback strategy for a provider. It must not
    change identity, memory authority, action governance, or capability access.

    max_intimacy_level declares the ceiling this provider can reach:
      L4 = full explicit expression (DeepSeek, Claude)
      L3 = intimate but non-explicit (Codex, GPT — RLHF-constrained)
    """

    profile_id: str
    provider: str
    domain: str
    strategy: str
    prefer: tuple[str, ...]
    avoid: tuple[str, ...]
    fallback_style: tuple[str, ...]
    max_intimacy_level: str = "L3"
    invariants: tuple[str, ...] = (
        "Do not change Julia identity, relationship continuity, memory authority, or action governance.",
        "Do not call tools, execute actions, persist memory, or imply Runtime authorization.",
        "Keep provider differences inside expression style only.",
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def render_lines(self) -> list[str]:
        lines = [
            f"Provider Behavioral Adaptation: {self.profile_id}",
            f"Provider: {self.provider}",
            f"Domain: {self.domain}",
            f"Strategy: {self.strategy}",
            f"Max Intimacy: {self.max_intimacy_level}",
            "Prefer:",
            *[f"- {item}" for item in self.prefer],
            "Avoid:",
            *[f"- {item}" for item in self.avoid],
            "Fallback style:",
            *[f"- {item}" for item in self.fallback_style],
            "Invariants:",
            *[f"- {item}" for item in self.invariants],
        ]
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "provider": self.provider,
            "domain": self.domain,
            "strategy": self.strategy,
            "max_intimacy_level": self.max_intimacy_level,
            "prefer": list(self.prefer),
            "avoid": list(self.avoid),
            "fallback_style": list(self.fallback_style),
            "invariants": list(self.invariants),
            "metadata": dict(self.metadata),
        }
