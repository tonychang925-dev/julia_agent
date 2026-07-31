from __future__ import annotations

from pathlib import Path
from typing import Any

try:  # package import when called as runtime.cognitive.*
    from runtime.memory_loader import MemoryLoader
except ModuleNotFoundError:  # direct script/test path fallback
    from memory_loader import MemoryLoader

from .cognitive_context import JuliaContext


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
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent: {raw_line}")
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


class ContextBuilder:
    """Builds JuliaContext from persistent Julia state.

    This belongs to Julia Runtime, not to any provider. Providers receive the
    resulting JuliaContext and translate it into their own API format.
    """

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.identity_dir = self.project_root / "identity"
        self.memory_loader = MemoryLoader(self.project_root / "memory")

    def build(
        self,
        current_input: str,
        *,
        session_id: str | None = None,
        current_backend: str = "echo",
        mode: str = "conversation",
        voice_enabled: bool = True,
        conversation: dict[str, Any] | None = None,
        capability: dict[str, Any] | None = None,
        policy: dict[str, Any] | None = None,
        emotional_context: dict[str, Any] | None = None,
    ) -> JuliaContext:
        identity_yaml = self._load_identity_yaml()
        identity = {
            "yaml": identity_yaml,
            "personality": self._read_identity_doc("personality.md"),
            "values": self._read_identity_doc("values.md"),
            "specification": self._read_identity_doc("Julia Identity Specification v1.0.md"),
            "conversation_contract": self._read_identity_doc("conversation_contract.md"),
            "adult_intimacy_contract": self._read_identity_doc("adult_intimacy_contract.md"),
            "transcript_role": self._read_identity_doc("transcript_derived_role_definition.md"),
            "claude_diary_summary": self.memory_loader.get_diary_summary(),
        }
        relationship = identity_yaml.get("relationship", {}) if isinstance(identity_yaml, dict) else {}
        memory = self.memory_loader.retrieve(current_input)
        adaptive_emotional_context = emotional_context or self._derive_emotional_context(memory)
        return JuliaContext(
            identity=identity,
            relationship=relationship,
            memory=memory,
            conversation=conversation
            or {
                "session_id": session_id,
                "history": [],
            },
            capability=capability or {"tools": [], "voice": voice_enabled},
            policy=policy
            or {
                "language": "Chinese",
                "style": ["concise", "natural", "warm", "emotionally honest"],
                "memory_rule": "do not pretend unsupported facts",
            },
            runtime_state={
                "mode": mode,
                "voice_enabled": voice_enabled,
                "current_backend": current_backend,
                "session_id": session_id,
            },
            emotional_context=adaptive_emotional_context,
            current_input=current_input,
        )

    def _load_identity_yaml(self) -> dict[str, Any]:
        path = self.identity_dir / "julia_identity.yaml"
        return load_simple_yaml(path) if path.exists() else {}

    def _read_identity_doc(self, filename: str) -> str:
        path = self.identity_dir / filename
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @staticmethod
    def _derive_emotional_context(memory: list[dict[str, Any]]) -> dict[str, Any]:
        context = {
            "conversation_tone": "warm",
            "relationship_stage": "long_term",
            "interaction_style": "short_sentence",
        }
        contents = "\n".join(str(item.get("content", "")) for item in memory)
        if "先看架构" in contents or "架构设计" in contents or "architecture_first" in contents:
            context["interaction_style"] = "architecture_first"
            context["response_order"] = "architecture_then_code_detail"
        if "短句" in contents or "简洁" in contents:
            context["sentence_style"] = "short"
        return context
