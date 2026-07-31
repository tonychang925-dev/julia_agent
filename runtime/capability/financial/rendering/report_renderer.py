"""Markdown renderer for F1 premarket research reports."""

from __future__ import annotations

import runtime.capability.financial.contracts as c


def render_premarket_report(report: c.PremarketResearchReport) -> str:
    """Render a shadow report without recommendation language."""

    lines: list[str] = [
        f"# 《Julia盘前研究》{report.trade_date.isoformat()}",
        "",
        f"状态: {report.status}",
        f"Source Bundle: {report.source_bundle_id}",
        f"Input Hash: {report.input_hash}",
        "",
        "## 一、市场状态",
        _render_conclusion(report.market_summary),
        "",
        "## 二、今日主要矛盾",
        _render_conclusion(report.main_conflict),
        "",
        "## 三、重点题材",
    ]
    for idx, theme in enumerate(report.top_themes, 1):
        lines.append(
            f"{idx}. {theme.name} — {theme.attention_level} — {theme.lifecycle_stage} "
            f"{_render_refs(theme.evidence_refs)}"
        )
    lines.extend(["", "## 四、条件观察标的"])
    for idx, candidate in enumerate(report.conditional_watchlist, 1):
        lines.append(
            f"{idx}. {candidate.stock_name} ({candidate.stock_code}) — {candidate.observation_level}级 — "
            f"{candidate.strategy_id} {_render_refs(candidate.evidence_refs)}"
        )
    lines.extend(["", "## 五、风险与禁止项"])
    for item in report.risk_items:
        lines.append(f"- {_render_conclusion(item)}")
    for item in report.forbidden_items:
        lines.append(f"- {_render_conclusion(item)}")
    lines.extend(["", "## 六、集合竞价确认点"])
    for item in report.auction_confirmation_points:
        lines.append(f"- {_render_conclusion(item)}")
    lines.extend(["", "## 七、EvidenceRef"])
    for ref in report.evidence_refs:
        lines.append(f"- EvidenceRef: {ref.ref_id} ({ref.object_type}:{ref.object_id})")
    return "\n".join(lines).rstrip() + "\n"


def _render_conclusion(conclusion: c.ConclusionWithEvidence) -> str:
    return f"{conclusion.text} {_render_refs(conclusion.evidence_refs)}"


def _render_refs(refs: tuple[c.EvidenceRef, ...]) -> str:
    return "[" + ", ".join(f"EvidenceRef: {ref.ref_id}" for ref in refs) + "]"
