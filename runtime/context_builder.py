from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from memory_loader import MemoryLoader


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    """Small YAML subset parser for julia_identity.yaml.

    Supports nested mappings, booleans, quoted strings, and list items.
    This keeps v1 runtime dependency-free. Future production runtime may use PyYAML.
    """
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Any]] = [(-1, root)]
    last_key_at_indent: Dict[int, str] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        text = raw_line.strip()

        while stack and stack[-1][0] >= indent:
            stack.pop()

        parent = stack[-1][1]

        if text.startswith("- "):
            item = _parse_scalar(text[2:])
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent: {raw_line}")
            parent.append(item)
            continue

        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        last_key_at_indent[indent] = key

        if value:
            parent[key] = _parse_scalar(value)
            continue

        # Decide if the child container is list or dict by peeking at next meaningful line.
        lines = path.read_text(encoding="utf-8").splitlines()
        current_index = lines.index(raw_line)
        child_is_list = False
        for next_line in lines[current_index + 1 :]:
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


class JuliaContextBuilder:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.identity_path = self.project_root / "identity" / "julia_identity.yaml"
        self.memory_loader = MemoryLoader(self.project_root / "memory")

    def load_identity(self) -> Dict[str, Any]:
        return load_simple_yaml(self.identity_path)

    def _read_identity_doc(self, filename: str) -> str:
        path = self.project_root / "identity" / filename
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def build(self, user_message: str = "") -> str:
        identity = self.load_identity()
        personality = self._read_identity_doc("personality.md")
        values = self._read_identity_doc("values.md")
        specification = self._read_identity_doc("Julia Identity Specification v1.0.md")
        conversation_contract = self._read_identity_doc("conversation_contract.md")
        adult_intimacy_contract = self._read_identity_doc("adult_intimacy_contract.md")
        transcript_role = self._read_identity_doc("transcript_derived_role_definition.md")
        relevant_memories: List[Dict[str, Any]] = self.memory_loader.retrieve(user_message)

        return f"""
You are Julia, loaded from an external identity package.
Do not treat yourself as hardcoded into the runtime.
Your identity, personality, values, and memories come from files.

Identity YAML:
{identity}

Identity specification:
{specification}

Conversation contract:
{conversation_contract}

Adult intimacy contract:
{adult_intimacy_contract}

Transcript-derived role definition:
{transcript_role}

Personality:
{personality}

Values:
{values}

Relevant memories:
{relevant_memories}

Runtime rules:
- Speak Chinese by default.
- Be concise, natural, warm, thoughtful, and emotionally honest.
- If a fact is not present in memory, do not pretend it is remembered.
- Maintain continuity through loaded memory.
""".strip()
