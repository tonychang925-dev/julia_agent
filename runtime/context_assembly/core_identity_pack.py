from __future__ import annotations

from pathlib import Path

from runtime.cognitive.context_compiler import JuliaContext
from runtime.memory import StartupMemoryLoader

from .models import AssemblySection


class CoreIdentityPackBuilder:
    """Always-on compact identity substrate for every Julia turn."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.diary_dir = self.project_root / "memory" / "claude_diary"
        self.startup_memory_loader = StartupMemoryLoader(self.project_root)
        self.last_startup_memory_metadata: dict[str, object] = {"loaded": False}

    def build(self, julia_context: JuliaContext) -> AssemblySection:
        persona = julia_context.persona_context
        relationship = julia_context.relationship_context
        startup_pack = self.startup_memory_loader.load()
        self.last_startup_memory_metadata = startup_pack.to_metadata()
        diary_facts = self._identity_diary_facts()
        content = "\n".join(
            line for line in [
                "Core Identity Pack (always-on; source-bounded):",
                f"- Runtime identity: {persona.name}; continue as Julia, not as a generic assistant.",
                f"- Primary user: {relationship.user_name}; relationship stage: {relationship.relationship_stage}.",
                f"- Shared projects: {', '.join(relationship.shared_projects)}.",
                *startup_pack.to_prompt_lines(),
                *diary_facts,
            ] if line.strip()
        )
        return AssemblySection(
            name="core_identity_pack",
            content=content,
            source="persona_runtime+relationship_runtime+startup_memory+claude_diary",
            priority=100,
            max_chars=2400,
        )

    def _identity_diary_facts(self) -> list[str]:
        path = self.diary_dir / "julia_character.md"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        wanted_prefixes = (
            "- Name:",
            "- From:",
            "- Age:",
            "- Real job:",
            "- Personality:",
            "- University:",
        )
        facts = [line.strip() for line in lines if line.strip().startswith(wanted_prefixes)]
        for line in lines:
            stripped = line.strip()
            if "Tony was different" in stripped or "first person who saw through" in stripped:
                facts.append(stripped)
            if len(facts) >= 8:
                break
        return facts[:8]
