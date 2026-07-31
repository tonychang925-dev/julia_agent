from __future__ import annotations


class UnresolvedContextTracker:
    """Maintains open loops that should remain available in short-term continuity."""

    def detect_open_loops(self, user_text: str, topics: list[str]) -> list[dict[str, object]]:
        text = user_text.lower()
        loops: list[dict[str, object]] = []
        if "Project Pressure" in topics or any(signal in text for signal in ["做不完", "没完成", "完不成", "压力", "撑不住"]):
            loops.append({
                "topic": "project_completion",
                "status": "unresolved",
                "last_reference": user_text[:80],
                "importance": 0.8,
            })
        if "Health Follow-up" in topics and any(signal in text for signal in ["等", "之后", "忙完", "检查"]):
            loops.append({
                "topic": "health_followup",
                "status": "waiting",
                "last_reference": user_text[:80],
                "importance": 0.75,
            })
        if "e2e" in text and ("alpha" in text or "单轮" in text or "受治理" in text):
            loops.append({
                "topic": "E2E Integration Alpha",
                "status": "open",
                "goal": "validate single-step governed action pipeline",
                "constraints": [
                    "no long-term memory persistence",
                    "ask and reject must not execute",
                    "full trace required",
                ],
                "last_reference": user_text[:160],
                "importance": 0.9,
            })
        elif any(signal in text for signal in ["怎么办", "继续", "回头", "下一步"]):
            topic = topics[0] if topics else "conversation_followup"
            loops.append({
                "topic": topic,
                "status": "open",
                "last_reference": user_text[:80],
                "importance": 0.6,
            })
        return loops

    def merge(self, existing: list[dict[str, object]], new_items: list[dict[str, object]], *, limit: int = 8) -> list[dict[str, object]]:
        merged: dict[str, dict[str, object]] = {}
        for item in [*existing, *new_items]:
            topic = str(item.get("topic") or "").strip()
            if not topic:
                continue
            previous = merged.get(topic, {})
            if float(item.get("importance", 0.0) or 0.0) >= float(previous.get("importance", 0.0) or 0.0):
                merged[topic] = dict(item)
        return list(merged.values())[-limit:]
