from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from stt.finalizer import STTResult
from stt.wake_word_calibration import WakeWordAliasCorrector, WakeWordCalibrationStore


@dataclass(frozen=True)
class SpeechLabSTTConfig:
    speech_lab_root: Path = Path("/Users/admin/Desktop/speech_lab")
    stt_bin: Path | None = None
    lang: str = "zh-CN"
    auto_stop_ms: int = 1800
    max_duration_ms: int = 30000
    timeout_s: float = 45.0
    normalize: bool = True
    calibration_path: Path | None = None


class SpeechLabSTT:
    """Adapter around speech_lab's proven macOS Apple Speech STT binary."""

    def __init__(self, config: SpeechLabSTTConfig | None = None):
        self.config = config or SpeechLabSTTConfig()
        self.stt_bin = self.config.stt_bin or (self.config.speech_lab_root / "stt")
        self.calibration_store = WakeWordCalibrationStore(
            self.config.calibration_path or Path("/Users/admin/julia_agent/memory/wake_word_calibration.jsonl")
        )

    def capture_once(self) -> STTResult:
        started = perf_counter()
        if not self.stt_bin.exists():
            return STTResult(
                text="",
                ok=False,
                confidence=0.0,
                error=f"speech_lab stt binary not found: {self.stt_bin}",
            )
        env = dict(os.environ)
        env["JULIA_VOICE_AUTO_STOP_MS"] = str(self.config.auto_stop_ms)
        env["JULIA_VOICE_MAX_DURATION_MS"] = str(self.config.max_duration_ms)
        cmd = [
            str(self.stt_bin),
            "--lang",
            self.config.lang,
            "--no-retry",
            "--auto-stop-ms",
            str(self.config.auto_stop_ms),
            "--max-duration-ms",
            str(self.config.max_duration_ms),
        ]
        try:
            completed = subprocess.run(
                cmd,
                cwd=self.config.speech_lab_root if self.config.speech_lab_root.exists() else None,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.config.timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return STTResult(
                text="",
                ok=False,
                confidence=0.0,
                error=f"speech_lab stt timeout: {exc}",
            )

        raw_text = self._extract_text(completed.stdout, completed.stderr)
        text = self._normalize_text(raw_text) if self.config.normalize else raw_text
        if completed.returncode != 0 and not text:
            return STTResult(text="", ok=False, confidence=0.0, error=self._normalize_error(completed.stderr or completed.stdout))
        return STTResult(text=text, ok=bool(text), confidence=1.0 if text else 0.0, error=None if text else "未识别到文字")

    @staticmethod
    def _extract_text(stdout: str, stderr: str) -> str:
        stdout = (stdout or "").strip()
        if stdout:
            lines = [line.strip() for line in stdout.splitlines() if line.strip()]
            for line in reversed(lines):
                if not line.startswith("["):
                    return line
            return lines[-1] if lines else ""
        matches = re.findall(r"\[→\]\s*([^\r\n]+)", stderr or "")
        return matches[-1].strip() if matches else ""


    def _normalize_text(self, text: str) -> str:
        value = text.strip()
        if not value:
            return value
        value = WakeWordAliasCorrector(self.calibration_store).correct(value)
        value = self._apply_speech_lab_normalizer(value)
        value = self._fix_julia_wake_word(value)
        value = self._fix_identity_entities(value)
        value = self._repair_incomplete_wake_query(value)
        value = self._repair_semantic_confusions(value)
        return value

    def _apply_speech_lab_normalizer(self, text: str) -> str:
        dictionary_path = self.config.speech_lab_root / "config" / "dictionary.yaml"
        try:
            root = str(self.config.speech_lab_root)
            if root not in sys.path:
                sys.path.insert(0, root)
            from text.normalizer.normalizer import TextNormalizer  # type: ignore

            return TextNormalizer(dictionary_path).normalize(text)
        except Exception:
            return text.strip()

    @staticmethod
    def _fix_julia_wake_word(text: str) -> str:
        value = text.strip()
        # Apple Speech can mishear the English wake word "Julia" as "兄弟" in
        # Chinese utterances such as "Julia 你在吗". In Julia's dedicated voice
        # runtime, a leading wake-word-like "兄弟" followed by a direct address
        # is almost always intended as Julia. Keep this narrow to avoid changing
        # ordinary mentions of 兄弟 inside the sentence.
        aliases = [
            "Julia",
            "朱莉亚", "茱莉亚", "朱利亚", "朱丽亚", "朱丽娅",
            "茱丽亚", "茱丽娅", "朱莉娅", "茱莉娅", "朱莉雅",
            "茱莉雅", "朱利娅", "猪莉亚", "猪利亚", "朱莉呀",
            "茱莉呀", "助理呀", "助力呀", "助力了助力呀", "助理", "助力", "教练", "处理呀", "主力呀", "朱莉",
            "兄弟",
        ]
        direct_address = r"(?=(你|，|,|在|帮|看|我|今|有|。|吗|呀|啊|说|听|记得|继续|$|\s))"
        for alias in sorted(aliases, key=len, reverse=True):
            value = re.sub(rf"^{re.escape(alias)}{direct_address}", "Julia", value, flags=re.IGNORECASE)
        return value


    @staticmethod
    def _fix_identity_entities(text: str) -> str:
        value = text.strip()
        # Proper-noun repair only: Apple Speech may hear "Tony" as "偷你"
        # or "托你" in Julia's Chinese voice sessions. Keep this as identity
        # entity normalization, not intent/mode keyword routing.
        tony_aliases = ["托尼", "托你", "偷你"]
        for alias in tony_aliases:
            value = value.replace(alias, "Tony")
        # A very narrow one-character capture appears in phrases like
        # "Julia你知道偷是谁吗"; repair only when it is used as a named entity.
        value = re.sub(r"(?<=知道)偷(?=是谁)", "Tony", value)
        value = re.sub(r"(?<=认识)从(?=[。？！!?]|$)", "Tony", value)
        return value


    @staticmethod
    def _repair_incomplete_wake_query(text: str) -> str:
        value = text.strip()
        # Apple Speech may finalize too early and drop the tail of a very common
        # wake query: "Julia 你在吗" -> "Julia你。". Repair only this narrow
        # dedicated-wake pattern; do not alter longer content turns.
        if value in {"Julia你。", "Julia你", "Julia， 你。", "Julia， 你"}:
            return "Julia你在吗？"
        if value in {"Julia在。", "Julia在"}:
            return "Julia你在吗？"
        return value

    @staticmethod
    def _repair_semantic_confusions(text: str) -> str:
        value = text.strip()
        # Narrow speech-only repair from real session:
        # Tony asked about Julia saying “不那么慌”, Apple Speech produced
        # “为什么不那么花”. Only repair this fixed phrase, not general 花/慌.
        value = value.replace("不那么花", "不那么慌")
        return value

    @staticmethod
    def _normalize_error(raw: str) -> str:
        raw = (raw or "").strip()
        if "语音识别" in raw and "授权" in raw:
            return "Speech Recognition permission is not authorized. Enable it in System Settings > Privacy & Security > Speech Recognition."
        if "麦克风" in raw or "Microphone" in raw:
            return "Microphone permission or input device is unavailable."
        return raw.splitlines()[-1] if raw else "speech_lab stt failed"
