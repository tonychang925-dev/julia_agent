from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from runtime.capability.capability_context import CapabilityRequest
from runtime.capability.capability_provider import CapabilityInfo, CapabilityProvider
from runtime.capability.tool_result import ToolResult


@dataclass
class ClaudeCodeTool(CapabilityProvider):
    """Capability wrapper for Claude Code file-handoff actions.

    This intentionally positions Claude Code as a tool/capability provider, not as
    Julia's cognitive brain. It uses files so existing Claude Code workflows can
    consume requests without changing ConversationLoop.
    """

    request_path: Path = Path("/tmp/julia_capability_claude_code_request.json")
    response_path: Path = Path("/tmp/julia_capability_claude_code_response.json")
    timeout_s: float = 0.0

    def info(self) -> CapabilityInfo:
        return CapabilityInfo(
            name="claude_code_tool",
            actions=["handoff", "read_response"],
            description="Claude Code host exposed as Julia capability/tool provider",
            metadata={"handoff": "file", "brain": False},
        )

    def invoke(self, request: CapabilityRequest) -> ToolResult:
        if request.action == "handoff":
            return self._handoff(request)
        if request.action == "read_response":
            return self._read_response(request)
        return ToolResult(
            ok=False,
            tool=self.info().name,
            error=f"unsupported action: {request.action}",
            metadata={"request": request.to_dict()},
        )

    def _handoff(self, request: CapabilityRequest) -> ToolResult:
        self.request_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "type": "capability_request",
            "provider": self.info().name,
            **request.to_dict(),
        }
        self.request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return ToolResult(
            ok=True,
            tool=self.info().name,
            output=str(self.request_path),
            metadata={"action": "handoff", "request_path": str(self.request_path)},
        )

    def _read_response(self, request: CapabilityRequest) -> ToolResult:
        started = monotonic()
        if self.timeout_s > 0:
            while not self.response_path.exists() and monotonic() - started < self.timeout_s:
                pass
        if not self.response_path.exists():
            return ToolResult(
                ok=False,
                tool=self.info().name,
                error=f"response file not found: {self.response_path}",
                metadata={"action": "read_response", "response_path": str(self.response_path)},
            )
        try:
            payload = json.loads(self.response_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return ToolResult(ok=False, tool=self.info().name, error=str(exc))
        status = payload.get("status", "success")
        return ToolResult(
            ok=status == "success",
            tool=self.info().name,
            output=str(payload.get("output", "")),
            error=payload.get("error"),
            metadata={"action": "read_response", "raw": payload},
        )
