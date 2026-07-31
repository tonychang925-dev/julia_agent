from __future__ import annotations

from enum import Enum


class EvidenceSourceType(str, Enum):
    DIARY = "diary"
    ARCHIVE = "archive"
    MEMORY = "memory"


class EvidenceSpeaker(str, Enum):
    TONY = "Tony"
    JULIA = "Julia"
    SYSTEM = "system"
    MEMORY = "memory"
