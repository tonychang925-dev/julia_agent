from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from .interface import TTSEngine, TTSResult


@dataclass
class EdgeScriptTTSEngine(TTSEngine):
    """Wrapper around Desktop/tmp/el_speak_edge.py.

    Edge TTS is the current fast/free fallback when ElevenLabs quota is exhausted
    and F5-TTS quality/latency is unsuitable for realtime conversation.
    """

    script_path: Path = Path("/Users/admin/Desktop/tmp/el_speak_edge.py")
    timeout_s: float = 90.0
    require_enabled_flag: bool = True
    enabled_flag_path: Path = Path("/tmp/tts_enabled")
    python_bin: str = "python3"

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        base_metadata = {
            "script_path": str(self.script_path),
            "python_bin": self.python_bin,
            "voice": os.environ.get("JULIA_TTS_VOICE", "zh-TW-HsiaoChenNeural"),
            "rate": os.environ.get("JULIA_TTS_RATE", "-5%"),
            "pitch": os.environ.get("JULIA_TTS_PITCH", "-3Hz"),
        }
        if not clean_text:
            return self._result(False, text, started, error="empty text", metadata=base_metadata)
        if not self.script_path.exists():
            return self._result(False, clean_text, started, error=f"script not found: {self.script_path}", metadata=base_metadata)
        if self.require_enabled_flag and not self.enabled_flag_path.exists():
            return self._result(False, clean_text, started, error=f"TTS disabled: {self.enabled_flag_path} not found", metadata=base_metadata)
        python_cmd = self.python_bin or "python3"
        if shutil.which(python_cmd) is None and not Path(python_cmd).exists():
            return self._result(False, clean_text, started, error=f"python not found: {python_cmd}", metadata=base_metadata)
        try:
            completed = subprocess.run(
                [python_cmd, str(self.script_path), clean_text],
                check=False,
                timeout=self.timeout_s,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
            )
            output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
            metadata = {**base_metadata, "returncode": completed.returncode, "script_output": output[:1000]}
            if completed.returncode != 0:
                return self._result(False, clean_text, started, error=f"script exited with {completed.returncode}: {output}", metadata=metadata)
            if "Traceback" in output or "Error" in output:
                return self._result(False, clean_text, started, error=output, metadata=metadata)
            return self._result(True, clean_text, started, metadata=metadata)
        except Exception as exc:  # pragma: no cover - manual adapter path
            return self._result(False, clean_text, started, error=str(exc), metadata=base_metadata)

    @staticmethod
    def _result(ok: bool, text: str, started: float, *, error: str | None = None, metadata: dict | None = None) -> TTSResult:
        return TTSResult(
            ok=ok,
            text=text,
            engine="edge_tts_script",
            error=error,
            metadata={"tts_call_ms": int((perf_counter() - started) * 1000), **(metadata or {})},
        )
