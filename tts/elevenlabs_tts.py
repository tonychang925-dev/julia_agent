from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from time import perf_counter
from pathlib import Path

from .interface import TTSEngine, TTSResult


@dataclass
class ElevenLabsScriptTTSEngine(TTSEngine):
    """Verified wrapper around the existing el_speak.py script.

    The script can exit 0 without playing audio when /tmp/tts_enabled or
    ELEVENLABS_API_KEY is missing. This adapter performs preflight checks and
    captures script output so Conversation Runtime does not mark silent failures
    as successful speech.
    """

    script_path: Path = Path("/Users/admin/Desktop/tmp/el_speak.py")
    timeout_s: float = 180.0
    require_enabled_flag: bool = True
    enabled_flag_path: Path = Path("/tmp/tts_enabled")

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        base_metadata = {"script_path": str(self.script_path)}
        if not clean_text:
            return self._result(False, text, started, error="empty text", metadata=base_metadata)
        if not self.script_path.exists():
            return self._result(False, clean_text, started, error=f"script not found: {self.script_path}", metadata=base_metadata)
        if self.require_enabled_flag and not self.enabled_flag_path.exists():
            return self._result(
                False,
                clean_text,
                started,
                error=f"TTS disabled: {self.enabled_flag_path} not found",
                metadata={**base_metadata, "enabled_flag": str(self.enabled_flag_path)},
            )
        if not os.environ.get("ELEVENLABS_API_KEY", ""):
            return self._result(False, clean_text, started, error="ELEVENLABS_API_KEY is not configured", metadata=base_metadata)
        if shutil.which("ffplay") is None:
            return self._result(False, clean_text, started, error="ffplay not found in PATH", metadata=base_metadata)
        try:
            completed = subprocess.run(
                ["python3", str(self.script_path), clean_text],
                check=False,
                timeout=self.timeout_s,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
            metadata = {**base_metadata, "returncode": completed.returncode, "script_output": output[:1000]}
            if completed.returncode != 0:
                return self._result(False, clean_text, started, error=f"script exited with {completed.returncode}: {output}", metadata=metadata)
            if "TTS Error:" in output or "API Error:" in output:
                return self._result(False, clean_text, started, error=output, metadata=metadata)
            return self._result(True, clean_text, started, metadata=metadata)
        except Exception as exc:  # pragma: no cover - manual adapter path
            return self._result(False, clean_text, started, error=str(exc), metadata=base_metadata)

    @staticmethod
    def _result(ok: bool, text: str, started: float, *, error: str | None = None, metadata: dict | None = None) -> TTSResult:
        return TTSResult(
            ok=ok,
            text=text,
            engine="elevenlabs_script",
            error=error,
            metadata={"tts_call_ms": int((perf_counter() - started) * 1000), **(metadata or {})},
        )
