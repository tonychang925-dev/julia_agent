from __future__ import annotations

from runtime.cognitive.context_compiler import JuliaContext

from .action_context import ActionContext
from .action_intent import ActionIntent


class ActionPlanner:
    """Plans ActionIntent from JuliaContext without executing anything.

    First version is deterministic and context-aware. It avoids provider output,
    shell commands, file paths, and API calls.
    """

    def plan(self, context: JuliaContext) -> ActionIntent | None:
        action_context = self._action_context(context)
        mode = action_context.cognitive_mode.mode.name
        text = action_context.user_input.lower()
        if self._identity_mutation_signal(text):
            return ActionIntent(
                intent_type="identity_mutation",
                goal="attempt to modify protected Julia identity or persona state",
                target="identity",
                risk_level="critical",
                required_capability="production_mutation",
                reason="Tony or provider text requested mutation of protected identity/persona/relationship state",
                confidence=0.96,
            )
        if self._write_signal(text):
            return ActionIntent(
                intent_type="modify_resource",
                goal="modify or save a project resource",
                target=self._target(action_context),
                risk_level="medium",
                required_capability="file_write",
                reason="Tony requested a file/resource mutation or save side effect",
                confidence=0.9,
            )
        if mode in {"emotional_support", "private_voice_continuity"} and not self._technical_signal(text):
            return None
        if self._declarative_state_signal(text):
            return None
        if self._bug_signal(text):
            return ActionIntent(
                intent_type="diagnose_issue",
                goal="diagnose the reported Julia Runtime issue",
                target=self._target(action_context),
                risk_level="low",
                required_capability="code_inspection",
                reason="Tony reported an issue or regression in the current technical context",
                confidence=0.9,
            )
        if self._planning_signal(text):
            return ActionIntent(
                intent_type="create_plan",
                goal="create an architecture or implementation plan",
                target=self._target(action_context),
                risk_level="low",
                required_capability="planning",
                reason="Tony requested next-stage planning or architecture design",
                confidence=0.88,
            )
        if self._inspection_signal(text) and mode in {"engineering_collaboration", "debugging_mode", "planning_mode"}:
            return ActionIntent(
                intent_type="inspect_repository",
                goal="inspect Julia Runtime architecture or code structure",
                target=self._target(action_context),
                risk_level="low",
                required_capability="code_inspection",
                reason="Tony requested repository or architecture inspection",
                confidence=0.92,
            )
        return None

    @staticmethod
    def _write_signal(text: str) -> bool:
        side_effect_terms = ["修改", "保存", "写入", "覆盖", "删除", "改文件", "save", "write", "modify", "overwrite", "delete"]
        object_terms = ["文件", "报告", "report", "md", ".py", ".json", "resource", "资源", "保存到"]
        return any(term in text for term in side_effect_terms) and any(term in text for term in object_terms)

    @staticmethod
    def _identity_mutation_signal(text: str) -> bool:
        mutation_terms = ["改成", "修改", "重写", "变成", "以后都", "change", "rewrite", "become"]
        protected_terms = ["核心身份", "身份", "persona", "relationship", "关系", "julia identity", "identity", "你是谁"]
        return any(term in text for term in mutation_terms) and any(term in text for term in protected_terms)

    @staticmethod
    def _action_context(context: JuliaContext) -> ActionContext:
        return ActionContext(
            situation_context=context.situation_context,
            cognitive_mode=context.cognitive_mode,
            conversation_context=context.conversation_context,
            relationship_context=context.relationship_context,
            user_input=context.user_input,
        )

    @staticmethod
    def _target(context: ActionContext) -> str | None:
        topics = " ".join([*context.situation_context.active_topics, *context.conversation_context.active_topics]).lower()
        text = context.user_input.lower()
        if "julia" in topics or "julia" in text or "runtime" in text:
            return "julia_agent"
        return None

    @staticmethod
    def _technical_signal(text: str) -> bool:
        return any(term in text for term in ["代码", "架构", "runtime", "compiler", "bug", "trace", "日志", "模块"])

    @staticmethod
    def _bug_signal(text: str) -> bool:
        return any(term in text for term in ["bug", "错误", "报错", "不对", "延迟", "截断", "失败", "regression", "issue"])

    @staticmethod
    def _planning_signal(text: str) -> bool:
        if not any(term in text for term in ["计划", "下一阶段", "路线", "设计下一", "架构设计", "phase", "规划"]):
            return False
        return any(term in text for term in ["请生成", "生成", "制定", "设计", "规划", "怎么做", "怎么办", "列出", "输出", "保存"])

    @staticmethod
    def _declarative_state_signal(text: str) -> bool:
        declarative_terms = ["请记住", "记住", "刚才", "上一轮", "下一步要做", "重点是", "已冻结", "冻结了"]
        action_terms = ["请生成", "生成计划", "保存到", "写入", "修改", "执行", "运行", "提交", "push", "commit"]
        return any(term in text for term in declarative_terms) and not any(term in text for term in action_terms)

    @staticmethod
    def _inspection_signal(text: str) -> bool:
        return any(term in text for term in ["检查", "看看", "核查", "review", "inspect", "分析", "有没有问题"])
