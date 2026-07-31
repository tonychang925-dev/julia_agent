from __future__ import annotations

from pathlib import Path
from typing import Any

from .persona_context import PersonaSource


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Small YAML subset parser used by Julia identity files.

    Keeps Persona Runtime dependency-free and avoids adding a PyYAML dependency
    for Phase 3.5.1.
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    lines = path.read_text(encoding="utf-8").splitlines()

    for index, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        text = raw_line.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if text.startswith("- "):
            if isinstance(parent, list):
                parent.append(_parse_scalar(text[2:]))
            continue
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _parse_scalar(value)
            continue
        child_is_list = False
        for next_line in lines[index + 1 :]:
            if not next_line.strip() or next_line.lstrip().startswith("#"):
                continue
            next_indent = len(next_line) - len(next_line.lstrip(" "))
            if next_indent <= indent:
                break
            child_is_list = next_line.strip().startswith("- ")
            break
        child: Any = [] if child_is_list else {}
        parent[key] = child
        stack.append((indent, child))
    return root


class PersonaLoader:
    """Loads persistent Julia identity files into PersonaSource."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.identity_dir = self.project_root / "identity"

    def load(self) -> PersonaSource:
        return PersonaSource(
            identity_yaml=self._load_identity_yaml(),
            personality_text=self._read_identity_doc("personality.md"),
            values_text=self._read_identity_doc("values.md"),
            conversation_contract_text=self._read_identity_doc("conversation_contract.md"),
        )

    def _load_identity_yaml(self) -> dict[str, Any]:
        path = self.identity_dir / "julia_identity.yaml"
        if not path.exists():
            return {}
        return load_simple_yaml(path)

    def _read_identity_doc(self, filename: str) -> str:
        path = self.identity_dir / filename
        return path.read_text(encoding="utf-8") if path.exists() else ""
