from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssemblySection:
    name: str
    content: str
    source: str
    priority: int
    max_chars: int

    def clipped(self) -> "AssemblySection":
        text = self.content.strip()
        if self.max_chars > 0 and len(text) > self.max_chars:
            text = text[: self.max_chars].rstrip() + "…"
        return AssemblySection(
            name=self.name,
            content=text,
            source=self.source,
            priority=self.priority,
            max_chars=self.max_chars,
        )


@dataclass(frozen=True)
class AssembledContext:
    prompt_section: str
    metadata: dict[str, object] = field(default_factory=dict)
