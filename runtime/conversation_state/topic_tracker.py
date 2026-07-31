from __future__ import annotations


class TopicTracker:
    """Tracks topic lifecycle signals for continuity.

    This first version is deterministic and metadata-oriented. It is not a
    cognitive-mode classifier and does not decide private/relationship modes.
    """

    TOPIC_STATUS = ["introduced", "active", "paused", "resolved", "archived"]

    def extract_topics(self, *texts: str) -> list[str]:
        text = "\n".join(item for item in texts if item).lower()
        topics: list[str] = []
        topic_signals = [
            ("Julia Runtime", ["julia runtime", "julia", "runtime", "运行时"]),
            ("Cognitive Architecture", ["cognitive", "认知", "架构", "context", "compiler", "projection", "arbitration"]),
            ("Provider Migration", ["deepseek", "claude", "gpt", "gemini", "provider", "迁移", "模型"]),
            ("Project Pressure", ["压力", "做不完", "没完成", "完不成", "撑不住", "累", "overload", "pressure"]),
            ("Health Follow-up", ["身体", "健康", "检查", "睡眠", "不舒服", "health"]),
            ("Phase 3.7.4", ["phase 3.7.4", "3.7.4"]),
            ("E2E Integration Alpha", ["e2e integration alpha", "e2e alpha"]),
            ("Single-Step Governed E2E", ["单轮受治理", "single-step governed", "single step governed"]),
            ("Action Governance", ["ask/reject", "ask", "reject", "governance", "治理", "阻断"]),
            ("Trace Verification", ["完整 trace", "trace 验证", "intent trace", "execution trace", "reflection trace"]),
            ("Memory Persistence Boundary", ["不写长期 memory", "不写长期记忆", "memory persistence", "不持久化"]),
            ("Planning", ["计划", "下一步", "排期", "milestone", "phase"]),
            ("Debugging", ["bug", "错误", "修复", "trace", "日志", "截断", "不对"]),
        ]
        for topic, signals in topic_signals:
            if any(signal in text for signal in signals):
                topics.append(topic)
        return self._dedupe(topics)

    @staticmethod
    def _dedupe(items: list[str], *, limit: int = 8) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            value = str(item).strip()
            if value and value not in seen:
                seen.add(value)
                result.append(value)
            if len(result) >= limit:
                break
        return result
