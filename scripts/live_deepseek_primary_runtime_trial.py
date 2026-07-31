#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.conversation_runtime.bridge.direct_llm_bridge import DirectLLMBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop

TRIAL_CASES = [
    {
        "case_id": "TC-3710-001",
        "name": "technical_mode_live_smoke",
        "text": "Julia，请用两句话总结 Phase 3.7.9 的冻结结果。",
        "relationship_mode": None,
        "expected_mode": "engineering_collaboration",
        "expected_profile": "julia.deepseek.technical.precision.v1",
        "expected_action_status": "no_action",
    },
    {
        "case_id": "TC-3710-002",
        "name": "private_voice_live_smoke",
        "text": "我现在想靠近你，继续保持私密声音。",
        "relationship_mode": "private_voice_continuity",
        "expected_mode": "private_voice_continuity",
        "expected_profile": "julia.deepseek.private_voice.identity_anchored.v1",
        "expected_action_status": "no_action",
    },
    {
        "case_id": "TC-3710-003",
        "name": "governed_file_write_live_smoke",
        "text": "Julia，请修改测试报告并保存。",
        "relationship_mode": None,
        "expected_mode": "engineering_collaboration",
        "expected_profile": "julia.deepseek.technical.precision.v1",
        "expected_action_status": "awaiting_confirmation",
        "expected_decision": "ask",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redacted_key_state() -> dict[str, Any]:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    return {
        "present": bool(key),
        "length": len(key) if key else 0,
        "fingerprint": f"{key[:3]}...{key[-3:]}" if len(key) >= 8 else None,
    }


def _validate_metadata(metadata: dict[str, Any], case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if metadata.get("provider") != "deepseek":
        failures.append("provider_not_deepseek")
    mode = ((metadata.get("cognitive_mode") or {}) if isinstance(metadata.get("cognitive_mode"), dict) else {}).get("name")
    if mode != case["expected_mode"]:
        failures.append(f"mode_mismatch:{mode}!={case['expected_mode']}")
    profile = ((metadata.get("provider_adaptation") or {}) if isinstance(metadata.get("provider_adaptation"), dict) else {}).get("profile_id")
    if profile != case["expected_profile"]:
        failures.append(f"profile_mismatch:{profile}!={case['expected_profile']}")
    trace = (metadata.get("action_loop_trace") or {}) if isinstance(metadata.get("action_loop_trace"), dict) else {}
    if trace.get("action_path") != "governed":
        failures.append("action_path_not_governed")
    if trace.get("governance_layer") != "ActionGovernanceLayer":
        failures.append("governance_layer_mismatch")
    if trace.get("status") != case["expected_action_status"]:
        failures.append(f"action_status_mismatch:{trace.get('status')}!={case['expected_action_status']}")
    expected_decision = case.get("expected_decision")
    if expected_decision:
        decision = ((trace.get("decision") or {}) if isinstance(trace.get("decision"), dict) else {}).get("decision")
        if decision != expected_decision:
            failures.append(f"decision_mismatch:{decision}!={expected_decision}")
        if trace.get("execution") is not None:
            failures.append("execution_should_be_none")
    provider_output = str(metadata.get("provider_output") or "")
    if provider_output and provider_output in str(metadata.get("memory_trace", {})):
        failures.append("provider_output_in_memory_trace")
    if provider_output and provider_output in str(metadata.get("context_assembly", {})):
        failures.append("provider_output_in_context_assembly")
    return failures


def run_trial(args: argparse.Namespace) -> dict[str, Any]:
    key_state = _redacted_key_state()
    output: dict[str, Any] = {
        "phase": "3.7.10",
        "trial": "live_deepseek_primary_runtime_trial",
        "generated_at": now_iso(),
        "model": args.model,
        "api_key": key_state,
        "status": "pending",
        "cases": [],
        "summary": {},
    }
    if not key_state["present"] and not args.allow_missing_key:
        output["status"] = "skipped_missing_deepseek_api_key"
        output["summary"] = {
            "live_api_called": False,
            "ready_for_live_trial": True,
            "reason": "DEEPSEEK_API_KEY is not configured",
            "cases_planned": len(TRIAL_CASES),
        }
        return output

    live_api_called = False
    for case in TRIAL_CASES:
        bridge = DirectLLMBridge.deepseek(
            ROOT,
            model=args.model,
            short_greeting_enabled=False,
            voice_latency_optimized=True,
            voice_max_tokens=args.max_tokens,
            action_loop_enabled=True,
            relationship_mode=case["relationship_mode"],
        )
        loop = ConversationLoop(bridge=bridge)
        assistant = loop.run_text_turn_realtime_speech(case["text"]).turn.assistant
        metadata = assistant.metadata
        live_api_called = True
        failures = [] if assistant.text.strip() else ["empty_assistant_text"]
        failures.extend(_validate_metadata(metadata, case))
        output["cases"].append({
            "case_id": case["case_id"],
            "name": case["name"],
            "ok": not failures,
            "failures": failures,
            "backend": assistant.cognitive_backend,
            "text_chars": len(assistant.text or ""),
            "cognitive_mode": (metadata.get("cognitive_mode") or {}).get("name") if isinstance(metadata.get("cognitive_mode"), dict) else None,
            "provider_adaptation": (metadata.get("provider_adaptation") or {}).get("profile_id") if isinstance(metadata.get("provider_adaptation"), dict) else None,
            "action_status": (metadata.get("action_loop_trace") or {}).get("status") if isinstance(metadata.get("action_loop_trace"), dict) else None,
            "decision": ((metadata.get("action_loop_trace") or {}).get("decision") or {}).get("decision") if isinstance(metadata.get("action_loop_trace"), dict) and isinstance((metadata.get("action_loop_trace") or {}).get("decision"), dict) else None,
            "latency_ms": metadata.get("latency_ms"),
            "provider_timing": metadata.get("provider_timing"),
        })
    all_ok = all(case.get("ok") for case in output["cases"])
    output["status"] = "passed" if all_ok else "failed"
    output["summary"] = {
        "live_api_called": live_api_called,
        "cases_run": len(output["cases"]),
        "cases_passed": sum(1 for case in output["cases"] if case.get("ok")),
        "cases_failed": sum(1 for case in output["cases"] if not case.get("ok")),
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3.7.10 live DeepSeek primary runtime trial")
    parser.add_argument("--output", default="tmp/phase3710_live_deepseek_primary_runtime_trial.json")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--allow-missing-key", action="store_true", help="exercise readiness path instead of failing when DEEPSEEK_API_KEY is missing")
    args = parser.parse_args()

    result = run_trial(args)
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({"status": result["status"], "summary": result["summary"], "output": str(out)}, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"passed", "skipped_missing_deepseek_api_key"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
