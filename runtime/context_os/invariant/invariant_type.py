from __future__ import annotations

from enum import Enum


class InvariantType(str, Enum):
    IDENTITY = "identity"
    PERSONA = "persona"
    RELATIONSHIP = "relationship"
    COGNITIVE_OWNERSHIP = "cognitive_ownership"
    GOVERNED_MEMORY = "governed_memory"
    PROJECT_CONTINUITY = "project_continuity"
    PROVIDER_INDEPENDENCE = "provider_independence"
