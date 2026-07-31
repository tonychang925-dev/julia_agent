from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.persona.persona_loader import load_simple_yaml

from .relationship_context import RelationshipSource
from .relationship_store import RelationshipStore


class RelationshipLoader:
    """Loads persistent relationship inputs for Relationship Runtime."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.identity_dir = self.project_root / "identity"
        self.store = RelationshipStore(self.project_root)

    def load(self) -> RelationshipSource:
        return RelationshipSource(
            identity_yaml=self._load_identity_yaml(),
            conversation_contract_text=self._read_identity_doc("conversation_contract.md"),
            state=self.store.load_state(),
        )

    def _load_identity_yaml(self) -> dict[str, Any]:
        path = self.identity_dir / "julia_identity.yaml"
        if not path.exists():
            return {}
        return load_simple_yaml(path)

    def _read_identity_doc(self, filename: str) -> str:
        path = self.identity_dir / filename
        return path.read_text(encoding="utf-8") if path.exists() else ""
