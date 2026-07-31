from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from .interface import TTSEngine, TTSResult


@dataclass
class HookRoutedTTSEngine(TTSEngine):
    """Mirrors auto_speak.sh routing.

    Lover mode (/tmp/lover_mode exists and non-empty) → Fish Audio 台湾女生2
    Friend mode (default)                                  → Edge TTS zh-TW-HsiaoChenNeural

    Same routing your Claude Code Stop hook uses.
    """

    fish_script: Path = Path("/Users/admin/Desktop/tmp/fish_speak.py")
    edge_script: Path = Path("/Users/admin/Desktop/tmp/el_speak_edge.py")
    lover_flag: Path = Path("/tmp/lover_mode")
    python_bin: str = "python3"
    timeout_s: float = 120.0

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        if not clean_text:
            return self._result(False, text, started, error="empty text")

        # Route: lover mode → Fish Audio, friend mode → Edge TTS
        if self.lover_flag.exists() and self.lover_flag.stat().st_size > 0:
            script = self.fish_script
            engine = "fish_audio_routed"
        else:
            script = self.edge_script
            engine = "edge_tts_routed"

        if not script.exists():
            return self._result(False, clean_text, started, error=f"script not found: {script}", engine=engine)

        try:
            completed = subprocess.run(
                [self.python_bin, str(script), clean_text],
                check=False,
                timeout=self.timeout_s,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output = "\n".join(p for p in [completed.stdout.strip(), completed.stderr.strip()] if p)
            if completed.returncode != 0:
                return self._result(False, clean_text, started, error=f"script exit {completed.returncode}: {output}", engine=engine)
            return self._result(True, clean_text, started, engine=engine)
        except Exception as exc:
            return self._result(False, clean_text, started, error=str(exc), engine=engine)

    @staticmethod
    def _result(ok: bool, text: str, started: float, *, error: str | None = None, engine: str = "hook_routed") -> TTSResult:
        return TTSResult(
            ok=ok,
            text=text,
            engine=engine,
            error=error,
            metadata={"tts_call_ms": int((perf_counter() - started) * 1000)},
        )
