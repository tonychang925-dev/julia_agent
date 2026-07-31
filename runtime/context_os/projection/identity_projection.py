from __future__ import annotations

from dataclasses import dataclass

from .projection_block import ContextProjectionBlock


@dataclass
class IdentityProjection:
    def project(self, content: str | None) -> list[ContextProjectionBlock]:
        if not content:
            return []
        return [ContextProjectionBlock(
            block_id="projection_identity_core",
            block_type="core_identity",
            source_refs=["core_identity"],
            content=content,
            priority=100,
            authority=0.98,
            required=True,
            metadata={"projection": "identity", "reason": "identity_always_present"},
        )]
