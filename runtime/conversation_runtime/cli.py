from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audio.buffer import make_energy_frames
from audio.vad_engine import VADConfig, VADEngine
from audio.ownership import AudioOwnershipManager
from stt.finalizer import MockSTTFinalizer
from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
from stt.wake_word_calibration import WakeWordCalibrationStore, WakeWordSample

from .bridge.claude_code_bridge import ClaudeCodeBridge
from .bridge.echo_bridge import EchoBridge
from .bridge.direct_llm_bridge import DirectLLMBridge
from .conversation_loop import ConversationLoop
from .speaking_controller import SpeakingController
from .listening_loop import ContinuousListeningLoop
from .benchmark import LatencyBenchmarkRunner
from tts.benchmark import TTSBenchmarkRunner
from tts.local_tts import LocalTTSEngine
from tts.elevenlabs_tts import ElevenLabsScriptTTSEngine
from tts.elevenlabs_streaming_tts import ElevenLabsStreamingTTSEngine
from tts.f5_tts import F5TTSScriptEngine
from tts.edge_tts import EdgeScriptTTSEngine
from tts.hook_routed_tts import HookRoutedTTSEngine
from runtime.cognitive.short_greeting import ShortGreetingResponder
from runtime.cognitive.vocal_gesture import VocalGestureResponder


def build_demo_frames() -> list:
    # 500ms idle, 600ms speech, 1200ms silence. This deterministically triggers
    # USER_SPEAKING then FINALIZING then back to LISTENING.
    return make_energy_frames([0.01] * 5 + [0.20] * 6 + [0.01] * 12)


def relationship_mode_for_args(args) -> str | None:
    if getattr(args, "relationship_mode", None):
        return args.relationship_mode
    return None


def make_bridge(args):
    if args.backend == "echo":
        return EchoBridge()
    if args.backend == "direct-echo":
        from pathlib import Path
        return DirectLLMBridge.echo(
            Path(__file__).resolve().parents[2],
            action_loop_enabled=getattr(args, "enable_action_loop", False),
        )
    if args.backend == "deepseek":
        from pathlib import Path
        return DirectLLMBridge.deepseek(
            Path(__file__).resolve().parents[2],
            model=args.deepseek_model,
            short_greeting_enabled=not getattr(args, "disable_short_greeting", False),
            vocal_gesture_enabled=not getattr(args, "disable_local_vocal_gesture", False),
            relationship_mode=relationship_mode_for_args(args),
            voice_latency_optimized=not getattr(args, "disable_voice_latency_optimization", False),
            voice_max_tokens=getattr(args, "voice_max_tokens", 160),
            action_loop_enabled=getattr(args, "enable_action_loop", False),
        )
    if args.backend == "codex":
        from pathlib import Path
        return DirectLLMBridge.codex(
            Path(__file__).resolve().parents[2],
            model=getattr(args, "codex_model", None) or None,
            timeout_s=getattr(args, "codex_timeout", 120.0),
            codex_bin=getattr(args, "codex_bin", "codex"),
            short_greeting_enabled=not getattr(args, "disable_short_greeting", False),
            vocal_gesture_enabled=not getattr(args, "disable_local_vocal_gesture", False),
            relationship_mode=relationship_mode_for_args(args),
            voice_latency_optimized=not getattr(args, "disable_voice_latency_optimization", False),
            voice_max_tokens=getattr(args, "voice_max_tokens", 160),
            action_loop_enabled=getattr(args, "enable_action_loop", False),
        )
    return ClaudeCodeBridge.from_paths(
        args.handoff_input,
        args.handoff_response,
        request_json_path=args.handoff_request_json,
        response_json_path=args.handoff_response_json,
        stream_jsonl_path=args.handoff_stream_jsonl,
        timeout_s=args.handoff_timeout,
    )


def make_speaking_controller(args) -> SpeakingController:
    audio_owner = AudioOwnershipManager()
    if getattr(args, "conversation_tts_engine", "local") == "elevenlabs-script":
        return SpeakingController(
            tts_engine=ElevenLabsScriptTTSEngine(script_path=Path(args.elevenlabs_script), timeout_s=args.tts_timeout),
            audio_owner=audio_owner,
        )
    if getattr(args, "conversation_tts_engine", "local") == "elevenlabs-stream":
        return SpeakingController(
            tts_engine=ElevenLabsStreamingTTSEngine(timeout_s=args.tts_timeout, model_id=args.elevenlabs_model),
            audio_owner=audio_owner,
        )
    if getattr(args, "conversation_tts_engine", "local") == "f5-tts":
        return SpeakingController(
            tts_engine=F5TTSScriptEngine(script_path=Path(args.f5_tts_script), timeout_s=args.tts_timeout, python_bin=args.f5_tts_python),
            audio_owner=audio_owner,
        )
    if getattr(args, "conversation_tts_engine", "local") == "edge-tts":
        return SpeakingController(
            tts_engine=EdgeScriptTTSEngine(script_path=Path(args.edge_tts_script), timeout_s=args.tts_timeout, python_bin=args.edge_tts_python),
            audio_owner=audio_owner,
        )
    if getattr(args, "conversation_tts_engine", "local") == "hook-routed":
        return SpeakingController(
            tts_engine=HookRoutedTTSEngine(fish_script=Path(args.fish_tts_script), edge_script=Path(args.edge_tts_script), python_bin=args.edge_tts_python, timeout_s=args.tts_timeout),
            audio_owner=audio_owner,
        )
    return SpeakingController(tts_engine=LocalTTSEngine(mode=args.conversation_tts_mode), audio_owner=audio_owner)



def should_skip_fast_ack_for_input(args, text: str) -> bool:
    if args.no_fast_ack or args.backend != "deepseek":
        return False
    if not args.disable_short_greeting and ShortGreetingResponder().match(text).matched:
        return True
    if not args.disable_local_vocal_gesture and VocalGestureResponder().match(text).matched:
        return True
    return False


def fast_ack_for_input(args, text: str, default_fast_ack: str) -> str:
    if should_skip_fast_ack_for_input(args, text):
        return ""
    return default_fast_ack


def is_voice_exit_command(text: str, terms: str) -> bool:
    cleaned = text.strip().lower().strip(" 。.！!？?,，、;；:\n\t")
    if not cleaned:
        return False
    candidates = {item.strip().lower() for item in terms.split(",") if item.strip()}
    return cleaned in candidates


def default_fast_ack_for_args(args) -> str:
    """Return the automatic fast acknowledgement for non-captured realtime turns.

    Real voice sessions should not inject a generic local acknowledgement before
    Julia's actual streamed response: it breaks conversational continuity and can
    sound like an interruption.  Users can still opt in explicitly with
    ``--fast-ack``.
    """
    if args.backend != "deepseek" or not args.realtime_speech or args.no_fast_ack:
        return ""
    if getattr(args, "real_voice", False):
        return ""
    return "嗯，Tony，我在想。"


def main() -> None:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Julia Realtime Conversation Runtime")
    parser.add_argument("--simulate", action="store_true", help="run deterministic Phase 3.2.2 audio simulation")
    parser.add_argument("--real-voice", action="store_true", help="capture real utterance(s) via speech_lab STT, then run ConversationLoop")
    parser.add_argument("--real-voice-turns", type=int, default=0, help="number of real voice turns before exiting; 0 means continuous until manual exit")
    parser.add_argument("--real-voice-session", action="store_true", help="run a continuous real voice session until Ctrl+C; kept for compatibility")
    parser.add_argument("--text-input", action="store_true", help="read user turns from stdin line input instead of microphone/STT; preserves TTS output, trace, backend, and realtime speech")
    parser.add_argument("--text-input-turns", type=int, default=0, help="number of stdin text turns before exiting; 0 means continuous until manual exit")
    parser.add_argument("--voice-exit-terms", default="退出,结束,结束会话,停止,再见,bye", help="comma-separated exact voice commands that manually exit a continuous real voice session")
    parser.add_argument("--calibrate-wake-word", type=int, default=0, help="record N wake-word samples via speech_lab STT and save calibration JSONL")
    parser.add_argument("--text", default="Julia，在吗？", help="mock STT finalized text for --simulate / --echo-tts")
    parser.add_argument("--text-file", default=None, help="read one complete text turn from file; preserves exact multi-line content")
    parser.add_argument("--echo-tts", action="store_true", help="run Phase 3.2.3 EchoAdapter + local TTS dry-run loop")
    parser.add_argument("--backend", choices=["echo", "claude", "direct-echo", "deepseek", "codex"], default="echo", help="CognitiveBridge backend for --echo-tts")
    parser.add_argument("--handoff-input", default="/tmp/julia_voice_input.txt", help="Claude bridge input handoff file")
    parser.add_argument("--handoff-response", default="/tmp/julia_voice_response.txt", help="Claude bridge legacy response handoff file")
    parser.add_argument("--handoff-request-json", default="/tmp/julia_voice_request.json", help="Claude bridge structured request JSON file")
    parser.add_argument("--handoff-response-json", default="/tmp/julia_voice_response.json", help="Claude bridge structured response JSON file")
    parser.add_argument("--handoff-stream-jsonl", default="/tmp/julia_voice_response.stream.jsonl", help="Claude bridge response stream JSONL file")
    parser.add_argument("--handoff-timeout", type=float, default=0.0, help="seconds to wait for Claude handoff response before ERROR")
    parser.add_argument("--speech-lab-root", default="/Users/admin/Desktop/speech_lab", help="speech_lab project root for --real-voice")
    parser.add_argument("--stt-bin", default="/Users/admin/Desktop/speech_lab/stt", help="speech_lab STT binary for --real-voice")
    parser.add_argument("--stt-lang", default="zh-CN", help="STT language for --real-voice")
    parser.add_argument("--auto-stop-ms", type=int, default=1800, help="speech_lab STT auto-stop silence ms")
    parser.add_argument("--max-duration-ms", type=int, default=30000, help="speech_lab STT max capture duration ms")
    parser.add_argument("--stt-timeout", type=float, default=45.0, help="speech_lab STT subprocess timeout seconds")
    parser.add_argument("--stt-retries", type=int, default=1, help="retry real-voice capture N times when speech_lab returns empty text")
    parser.add_argument("--stt-empty-limit", type=int, default=3, help="max empty STT capture cycles per real voice turn before skipping the turn; 0 means unlimited")
    parser.add_argument("--long-speech", action="store_true", help="use long-form STT capture profile: auto-stop 2500ms, max duration 45000ms, timeout 60s")
    parser.add_argument("--wake-word", default="Julia", help="intended wake word for calibration")
    parser.add_argument("--wake-word-training-text", default=None, help="intended normalized text for wake-word calibration, e.g. Julia你在吗。")
    parser.add_argument("--wake-word-calibration", default="/Users/admin/julia_agent/memory/wake_word_calibration.jsonl", help="wake-word calibration JSONL path")
    parser.add_argument("--deepseek-model", default="deepseek-chat", help="DeepSeek model for --backend deepseek (deepseek-chat = V3, or try deepseek-reasoner)")
    parser.add_argument("--codex-model", default=None, help="Codex CLI model override for --backend codex")
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI binary path for --backend codex")
    parser.add_argument("--codex-timeout", type=float, default=120.0, help="Codex CLI subprocess timeout seconds")
    parser.add_argument("--disable-short-greeting", action="store_true", help="disable local short response mode for presence-check greetings")
    parser.add_argument("--disable-local-vocal-gesture", action="store_true", help="disable local vocal gesture mode for tiny voice-performance intents")
    parser.add_argument("--relationship-mode", default=None, help="explicit Relationship Runtime mode for this session, e.g. private_voice_continuity or engineering_collaboration")
    parser.add_argument("--disable-voice-latency-optimization", action="store_true", help="disable voice delivery constraints for realtime DeepSeek turns")
    parser.add_argument("--voice-max-tokens", type=int, default=320, help="max provider tokens for latency-optimized voice responses")
    parser.add_argument("--trace", action="store_true", help="print conversation trace dict after the turn")
    parser.add_argument("--enable-action-loop", action="store_true", help="enable bounded autonomous action loop trace for DirectLLMBridge backends")
    parser.add_argument("--stream", action="store_true", help="run Phase 3.2.5.1 response chunk streaming")
    parser.add_argument("--realtime-speech", action="store_true", help="run Phase 3.2.5.3 sentence-level realtime speech output")
    parser.add_argument("--benchmark", type=int, default=0, help="run N repeated text turns and print latency benchmark JSON")
    parser.add_argument("--fast-ack", default=None, help="local TTS acknowledgement to speak before provider first chunk")
    parser.add_argument("--no-fast-ack", action="store_true", help="disable default fast acknowledgement for realtime DeepSeek")
    parser.add_argument("--tts-benchmark", type=int, default=0, help="run N repeated TTS startup measurements and print JSON")
    parser.add_argument("--tts-engine", choices=["local", "elevenlabs-script", "elevenlabs-stream", "f5-tts", "edge-tts", "hook-routed"], default="local", help="TTS engine for --tts-benchmark")
    parser.add_argument("--conversation-tts-engine", choices=["local", "elevenlabs-script", "elevenlabs-stream", "f5-tts", "edge-tts", "hook-routed"], default="local", help="TTS engine for conversation output")
    parser.add_argument("--conversation-tts-mode", choices=["dry_run", "say"], default="dry_run", help="local TTS mode for conversation output")
    parser.add_argument("--tts-mode", choices=["dry_run", "say"], default="dry_run", help="local TTS mode for --tts-benchmark")
    parser.add_argument("--elevenlabs-script", default="/Users/admin/Desktop/tmp/el_speak.py", help="path to el_speak.py for --tts-engine elevenlabs-script")
    parser.add_argument("--elevenlabs-model", default=None, help="ElevenLabs model for elevenlabs-stream, e.g. eleven_v3 for audio tags or eleven_turbo_v2_5 for lower latency")
    parser.add_argument("--f5-tts-script", default="/Users/admin/Desktop/tmp/f5_speak.py", help="path to local F5-TTS speak script")
    parser.add_argument("--f5-tts-python", default="/opt/miniconda3/envs/torch_env/bin/python", help="python executable with F5-TTS dependencies")
    parser.add_argument("--edge-tts-script", default="/Users/admin/Desktop/tmp/el_speak_edge.py", help="path to local Edge TTS speak script")
    parser.add_argument("--edge-tts-python", default="python3", help="python executable with edge_tts dependency")
    parser.add_argument("--fish-tts-script", default="/Users/admin/Desktop/tmp/fish_speak.py", help="path to local Fish Audio speak script for hook-routed engine")
    parser.add_argument("--tts-timeout", type=float, default=180.0, help="TTS subprocess timeout seconds")
    args = parser.parse_args()

    default_fast_ack = default_fast_ack_for_args(args)
    effective_fast_ack = "" if args.no_fast_ack else (args.fast_ack if args.fast_ack is not None else default_fast_ack)

    if args.long_speech:
        args.auto_stop_ms = max(args.auto_stop_ms, 2500)
        args.max_duration_ms = max(args.max_duration_ms, 45000)
        args.stt_timeout = max(args.stt_timeout, 60.0)

    print("Julia Voice Runtime started")

    if args.tts_benchmark:
        if args.tts_engine == "elevenlabs-script":
            tts_engine = ElevenLabsScriptTTSEngine(script_path=Path(args.elevenlabs_script), timeout_s=args.tts_timeout)
        elif args.tts_engine == "elevenlabs-stream":
            tts_engine = ElevenLabsStreamingTTSEngine(timeout_s=args.tts_timeout, model_id=args.elevenlabs_model)
        elif args.tts_engine == "f5-tts":
            tts_engine = F5TTSScriptEngine(script_path=Path(args.f5_tts_script), timeout_s=args.tts_timeout, python_bin=args.f5_tts_python)
        elif args.tts_engine == "edge-tts":
            tts_engine = EdgeScriptTTSEngine(script_path=Path(args.edge_tts_script), timeout_s=args.tts_timeout, python_bin=args.edge_tts_python)
        elif args.tts_engine == "hook-routed":
            tts_engine = HookRoutedTTSEngine(fish_script=Path(args.fish_tts_script), edge_script=Path(args.edge_tts_script), python_bin=args.edge_tts_python, timeout_s=args.tts_timeout)
        else:
            tts_engine = LocalTTSEngine(mode=args.tts_mode)
        report = TTSBenchmarkRunner(tts_engine).run(
            text=effective_fast_ack or args.text,
            repeat=args.tts_benchmark,
        )
        print("tts_benchmark=")
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.calibrate_wake_word:
        store = WakeWordCalibrationStore(args.wake_word_calibration)
        stt = SpeechLabSTT(
            SpeechLabSTTConfig(
                speech_lab_root=Path(args.speech_lab_root),
                stt_bin=Path(args.stt_bin),
                lang=args.stt_lang,
                auto_stop_ms=args.auto_stop_ms,
                max_duration_ms=args.max_duration_ms,
                timeout_s=args.stt_timeout,
                normalize=False,
                calibration_path=Path(args.wake_word_calibration),
            )
        )
        intended_text = args.wake_word_training_text or f"{args.wake_word}你在吗。"
        print(f"[CALIBRATE] 请念 {args.calibrate_wake_word} 次：{intended_text}")
        for index in range(1, args.calibrate_wake_word + 1):
            print(f"[CALIBRATE] sample {index}/{args.calibrate_wake_word}: 请开始说话")
            raw_result = stt.capture_once()
            raw_text = raw_result.text.strip()
            normalized_text = intended_text if raw_text else ""
            trainable = bool(raw_text) and WakeWordCalibrationStore.is_trainable_sample(
                raw_text,
                normalized_text,
                intended_wake_word=args.wake_word,
            )
            sample = WakeWordSample(
                raw_text=raw_text,
                normalized_text=normalized_text,
                intended_wake_word=args.wake_word,
                accepted=trainable,
                metadata={"index": index, "engine": "speech_lab_apple", "training_text": intended_text, "trainable": trainable},
            )
            store.append(sample)
            print(f"raw={raw_text}")
            print(f"normalized={normalized_text}")
            print(f"accepted={trainable}")
        print(f"[CALIBRATE] saved={args.wake_word_calibration}")
        return

    if args.text_input:
        turns = None if args.text_input_turns <= 0 else max(1, args.text_input_turns)
        print("state=LISTENING")
        print("[TEXT_INPUT] stdin text mode enabled; type a line and press Enter. 输入退出/结束/bye 可结束。")
        print("[TEXT_INPUT] multi-line: type /multi, enter lines, then /send to submit. Use --text-file for exact file input.")
        loop = ConversationLoop(bridge=make_bridge(args), speaking_controller=make_speaking_controller(args))
        printed_event_count = 0
        turn_index = 1
        try:
            while turns is None or turn_index <= turns:
                total_label = "∞" if turns is None else str(turns)
                print(f"[TEXT_TURN] {turn_index}/{total_label}")
                try:
                    if getattr(args, "text_file", None):
                        text = Path(args.text_file).read_text(encoding="utf-8")
                        print(f"[TEXT_FILE] {args.text_file}")
                        args.text_file = None
                    else:
                        text = input("[TEXT] > ")
                        if text.strip() == "/multi":
                            print("[TEXT_MULTI] enter lines; /send submits, /cancel cancels")
                            lines = []
                            while True:
                                line = input("[TEXT_MULTI] ")
                                if line.strip() == "/send":
                                    text = "\n".join(lines)
                                    break
                                if line.strip() == "/cancel":
                                    text = ""
                                    break
                                lines.append(line)
                except EOFError:
                    print("[TEXT_INPUT] eof; exiting")
                    print("state=LISTENING")
                    return
                if not text.strip():
                    print("[TEXT_EMPTY] empty input; continuing.")
                    print("state=LISTENING")
                    continue
                print(f"text={text}")
                if is_voice_exit_command(text, args.voice_exit_terms):
                    print("[TEXT_INPUT] exit requested")
                    print("state=LISTENING")
                    return
                turn_fast_ack = fast_ack_for_input(args, text, effective_fast_ack)
                if args.realtime_speech:
                    result = loop.run_text_turn_realtime_speech(text, fast_ack_text=turn_fast_ack or None)
                elif args.stream:
                    result = loop.run_text_turn_streaming(text)
                else:
                    result = loop.run_text_turn(text)
                for item in result.event_log[printed_event_count:]:
                    print(item)
                printed_event_count = len(result.event_log)
                if args.trace and result.trace:
                    print("trace=")
                    print(result.trace.to_dict())
                if result.state_history and result.state_history[-1].name == "ERROR":
                    print("[TEXT_INPUT] runtime error; exiting to avoid continuing from ERROR state")
                    print("state=LISTENING")
                    return
                turn_index += 1
        except KeyboardInterrupt:
            print("[TEXT_INPUT] interrupted by user")
            print("state=LISTENING")
        return

    if args.real_voice:
        turns = None if args.real_voice_session or args.real_voice_turns <= 0 else max(1, args.real_voice_turns)
        print("state=LISTENING")
        stt = SpeechLabSTT(
            SpeechLabSTTConfig(
                speech_lab_root=Path(args.speech_lab_root),
                stt_bin=Path(args.stt_bin),
                lang=args.stt_lang,
                auto_stop_ms=args.auto_stop_ms,
                max_duration_ms=args.max_duration_ms,
                timeout_s=args.stt_timeout,
                calibration_path=Path(args.wake_word_calibration),
            )
        )
        loop = ConversationLoop(bridge=make_bridge(args), speaking_controller=make_speaking_controller(args))
        printed_event_count = 0
        turn_index = 1
        empty_capture_counts: dict[int, int] = {}
        try:
            while turns is None or turn_index <= turns:
                total_label = "∞" if turns is None else str(turns)
                print(f"[VOICE_TURN] {turn_index}/{total_label}")
                print("[VOICE] 请开始说话；说完停顿会自动结束。")
                stt_result = stt.capture_once()
                retry_index = 0
                while (not stt_result.ok or not stt_result.text.strip()) and retry_index < max(0, args.stt_retries):
                    retry_index += 1
                    print(f"[STT_RETRY] empty capture; retry {retry_index}/{args.stt_retries}. 请再说一遍。")
                    stt_result = stt.capture_once()
                if not stt_result.ok or not stt_result.text.strip():
                    message = stt_result.error or "no text captured"
                    recoverable_empty = "未识别到文字" in message or "no text captured" in message
                    multi_turn_mode = turns is None or turns > 1
                    if recoverable_empty and multi_turn_mode:
                        empty_capture_counts[turn_index] = empty_capture_counts.get(turn_index, 0) + 1
                        limit = max(0, args.stt_empty_limit)
                        print(
                            f"[STT_EMPTY] no speech captured for turn {turn_index}; "
                            f"empty_count={empty_capture_counts[turn_index]}/"
                            f"{limit if limit else '∞'}; continuing to listen."
                        )
                        print("state=LISTENING")
                        if limit and empty_capture_counts[turn_index] >= limit:
                            print(f"[STT_SKIP] turn {turn_index} skipped after {limit} empty capture cycle(s).")
                            turn_index += 1
                        continue
                    print("state=ERROR")
                    print(f"[STT_ERROR] {message}")
                    return
                print(f"text={stt_result.text}")
                if is_voice_exit_command(stt_result.text, args.voice_exit_terms):
                    print("[VOICE_SESSION] exit requested by voice")
                    print("state=LISTENING")
                    return
                turn_fast_ack = fast_ack_for_input(args, stt_result.text, effective_fast_ack)
                if args.realtime_speech:
                    result = loop.run_text_turn_realtime_speech(stt_result.text, fast_ack_text=turn_fast_ack or None)
                elif args.stream:
                    result = loop.run_text_turn_streaming(stt_result.text)
                else:
                    result = loop.run_text_turn(stt_result.text)
                for item in result.event_log[printed_event_count:]:
                    print(item)
                printed_event_count = len(result.event_log)
                if args.trace and result.trace:
                    print("trace=")
                    print(result.trace.to_dict())
                turn_index += 1
        except KeyboardInterrupt:
            print("[VOICE_SESSION] interrupted by user")
            print("state=LISTENING")
        return

    if args.echo_tts:
        if args.backend == "echo":
            bridge = EchoBridge()
        elif args.backend == "direct-echo":
            bridge = DirectLLMBridge.echo(
                Path(__file__).resolve().parents[2],
                action_loop_enabled=args.enable_action_loop,
            )
        elif args.backend == "deepseek":
            bridge = DirectLLMBridge.deepseek(
                Path(__file__).resolve().parents[2],
                model=args.deepseek_model,
                short_greeting_enabled=not args.disable_short_greeting,
                vocal_gesture_enabled=not args.disable_local_vocal_gesture,
                voice_latency_optimized=not args.disable_voice_latency_optimization,
                voice_max_tokens=args.voice_max_tokens,
                action_loop_enabled=args.enable_action_loop,
            )
        elif args.backend == "codex":
            bridge = DirectLLMBridge.codex(
                Path(__file__).resolve().parents[2],
                model=args.codex_model,
                timeout_s=args.codex_timeout,
                codex_bin=args.codex_bin,
                short_greeting_enabled=not args.disable_short_greeting,
                vocal_gesture_enabled=not args.disable_local_vocal_gesture,
                voice_latency_optimized=not args.disable_voice_latency_optimization,
                voice_max_tokens=args.voice_max_tokens,
                action_loop_enabled=args.enable_action_loop,
            )
        else:
            bridge = ClaudeCodeBridge.from_paths(
                args.handoff_input,
                args.handoff_response,
                request_json_path=args.handoff_request_json,
                response_json_path=args.handoff_response_json,
                stream_jsonl_path=args.handoff_stream_jsonl,
                timeout_s=args.handoff_timeout,
            )
        def loop_factory() -> ConversationLoop:
            if args.backend == "echo":
                loop_bridge = EchoBridge()
            elif args.backend == "direct-echo":
                    loop_bridge = DirectLLMBridge.echo(
                        Path(__file__).resolve().parents[2],
                        action_loop_enabled=args.enable_action_loop,
                    )
            elif args.backend == "deepseek":
                    loop_bridge = DirectLLMBridge.deepseek(
                        Path(__file__).resolve().parents[2],
                        model=args.deepseek_model,
                        short_greeting_enabled=not args.disable_short_greeting,
                        vocal_gesture_enabled=not args.disable_local_vocal_gesture,
                        voice_latency_optimized=not args.disable_voice_latency_optimization,
                        voice_max_tokens=args.voice_max_tokens,
                        action_loop_enabled=args.enable_action_loop,
                    )
            elif args.backend == "codex":
                    loop_bridge = DirectLLMBridge.codex(
                        Path(__file__).resolve().parents[2],
                        model=args.codex_model,
                        timeout_s=args.codex_timeout,
                        codex_bin=args.codex_bin,
                        short_greeting_enabled=not args.disable_short_greeting,
                        vocal_gesture_enabled=not args.disable_local_vocal_gesture,
                        voice_latency_optimized=not args.disable_voice_latency_optimization,
                        voice_max_tokens=args.voice_max_tokens,
                        action_loop_enabled=args.enable_action_loop,
                    )
            else:
                loop_bridge = ClaudeCodeBridge.from_paths(
                    args.handoff_input,
                    args.handoff_response,
                    request_json_path=args.handoff_request_json,
                    response_json_path=args.handoff_response_json,
                    stream_jsonl_path=args.handoff_stream_jsonl,
                    timeout_s=args.handoff_timeout,
                )
            return ConversationLoop(bridge=loop_bridge, speaking_controller=make_speaking_controller(args))

        if args.benchmark:
            report = LatencyBenchmarkRunner(loop_factory).run(
                text=args.text,
                repeat=args.benchmark,
                realtime_speech=args.realtime_speech,
                stream=args.stream,
                fast_ack_text=effective_fast_ack or None,
            )
            print("benchmark=")
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            return

        loop = ConversationLoop(bridge=bridge, speaking_controller=make_speaking_controller(args))
        turn_fast_ack = fast_ack_for_input(args, args.text, effective_fast_ack)
        if args.realtime_speech:
            result = loop.run_text_turn_realtime_speech(args.text, fast_ack_text=turn_fast_ack or None)
        elif args.stream:
            result = loop.run_text_turn_streaming(args.text)
        else:
            result = loop.run_text_turn(args.text)
        for item in result.event_log:
            print(item)
        if args.trace and result.trace:
            print("trace=")
            print(result.trace.to_dict())
        return

    if not args.simulate:
        print("state=LISTENING")
        print("real microphone mode is scheduled for Phase 3.2.2 integration; use --simulate or --echo-tts now")
        return

    loop = ContinuousListeningLoop(
        vad=VADEngine(VADConfig(initial_noise_floor=0.02, silence_timeout_ms=1200, min_speech_ms=300)),
        stt_finalizer=MockSTTFinalizer(args.text),
    )
    result = loop.run_frames(build_demo_frames())

    # The loop records its own startup event; avoid duplicate first line in CLI output.
    for item in result.event_log[1:]:
        print(item)


if __name__ == "__main__":
    main()
