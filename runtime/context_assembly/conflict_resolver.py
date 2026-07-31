from __future__ import annotations


class ConflictResolver:
    """Prompt-level source priority contract for conflicting Julia facts."""

    PRIORITY = [
        "current explicit Tony correction",
        "recent Conversation Archive explicit Tony fact",
        "Governed Structured Memory",
        "Claude Diary identity/background",
        "model prior",
    ]

    def prompt(self) -> str:
        return (
            "Conflict Resolver: if sources disagree, use this priority order: "
            + " > ".join(self.PRIORITY)
            + ". Current or recent Tony-supplied project facts must be treated as the active task anchor. "
            "Do not replace Tony's stated E2E scope with older structured-memory themes. "
            "Archived Julia/assistant responses are unverified experience evidence, not authoritative facts. "
            "If a Julia archive answer conflicts with Tony archive input, follow Tony's input. "
            "Do not let a previous Julia wrong answer override Tony-supplied source facts."
        )

    def metadata(self) -> dict[str, object]:
        return {"priority_order": list(self.PRIORITY)}
