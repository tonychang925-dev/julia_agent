from __future__ import annotations

from dataclasses import dataclass

from runtime.cognitive.cognitive_context import JuliaContext

from .capability_context import CapabilityRequest
from .capability_router import CapabilityRouter
from .invocation_planner import CapabilityInvocationPlanner
from .permission import CapabilityPermissionGuard, PermissionDecision
from .reflection import ToolReflection, ToolReflectionBuilder
from .tool_result import ToolResult


@dataclass(frozen=True)
class CapabilityInvocationResult:
    request: CapabilityRequest | None
    permission: PermissionDecision | None
    tool_result: ToolResult | None
    reflection: ToolReflection | None

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict() if self.request else None,
            "permission": self.permission.to_dict() if self.permission else None,
            "tool_result": self.tool_result.to_dict() if self.tool_result else None,
            "reflection": self.reflection.to_dict() if self.reflection else None,
        }


@dataclass
class CapabilityInvocationRuntime:
    router: CapabilityRouter
    planner: CapabilityInvocationPlanner
    permission_guard: CapabilityPermissionGuard
    reflection_builder: ToolReflectionBuilder

    @classmethod
    def default(cls, router: CapabilityRouter) -> "CapabilityInvocationRuntime":
        return cls(
            router=router,
            planner=CapabilityInvocationPlanner(),
            permission_guard=CapabilityPermissionGuard(),
            reflection_builder=ToolReflectionBuilder(),
        )

    def run(self, context: JuliaContext) -> CapabilityInvocationResult:
        request = self.planner.plan(context)
        if request is None:
            return CapabilityInvocationResult(request=None, permission=None, tool_result=None, reflection=None)
        permission = self.permission_guard.decide(request)
        if not permission.allowed:
            blocked = ToolResult(
                ok=False,
                tool=request.capability,
                error=permission.reason,
                metadata={"permission": permission.to_dict()},
            )
            reflection = self.reflection_builder.build(request, blocked)
            return CapabilityInvocationResult(request=request, permission=permission, tool_result=blocked, reflection=reflection)
        result = self.router.invoke(request)
        reflection = self.reflection_builder.build(request, result)
        return CapabilityInvocationResult(request=request, permission=permission, tool_result=result, reflection=reflection)
