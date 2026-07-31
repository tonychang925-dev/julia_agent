from __future__ import annotations

from dataclasses import dataclass

from .voice_trace_validator import VoiceTraceValidationResult


@dataclass(frozen=True)
class JuliaBirthTestReport:
    title: str
    results: list[VoiceTraceValidationResult]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", f"Overall: {'PASS' if self.passed else 'FAIL'}", ""]
        for result in self.results:
            lines.append(f"## {result.scenario_id}")
            lines.append(f"Result: {'PASS' if result.passed else 'FAIL'}")
            lines.append("Checks:")
            for key, value in result.checks.items():
                lines.append(f"- {key}: {'✓' if value else '✗'}")
            if result.errors:
                lines.append(f"Errors: {', '.join(result.errors)}")
            lines.append("")
        return "\n".join(lines).strip()
