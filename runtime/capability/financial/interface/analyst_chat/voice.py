"""Voice placeholder for post-V0.1 analyst chat."""

VOICE_STATUS = "placeholder"


def voice_placeholder() -> dict[str, object]:
    return {"enabled": False, "status": VOICE_STATUS, "reason": "F4 V0.1 is text-only"}
