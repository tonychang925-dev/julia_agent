from __future__ import annotations

from .adaptation_profile import ProviderAdaptationProfile
from .profile_registry import profile_for


class ProviderBehaviorAdapter:
    """Injects provider-specific expression guidance without changing Runtime authority."""

    def adapt_messages(self, messages: list[dict[str, str]], *, provider: str, mode: str) -> tuple[list[dict[str, str]], ProviderAdaptationProfile]:
        profile = profile_for(provider, mode)
        adapted = [dict(message) for message in messages]
        if adapted:
            adapted[0]["content"] = f"{adapted[0].get('content', '')}\n\n" + "\n".join(profile.render_lines())
        return adapted, profile
