from __future__ import annotations

from dataclasses import dataclass, field

from .event import AgentEvent


@dataclass
class AgentEventGraph:
    events: list[AgentEvent] = field(default_factory=list)

    def add(self, event: AgentEvent) -> AgentEvent:
        self.events.append(event)
        return event

    def chain(self, event_type: str, payload: dict, *, parent: AgentEvent | None = None, correlation_id: str | None = None) -> AgentEvent:
        return self.add(
            AgentEvent(
                event_type=event_type,
                payload=payload,
                parent_id=parent.event_id if parent else None,
                correlation_id=correlation_id or (parent.correlation_id if parent else None),
            )
        )

    def to_list(self) -> list[dict]:
        return [event.to_dict() for event in self.events]
