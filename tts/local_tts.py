from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from time import perf_counter

from .interface import TTSEngine, TTSResult


@dataclass
class LocalTTSEngine(TTSEngine):
    """Local dependency-light TTS engine.

    `mode="dry_run"` is the Phase 3.2.3 default and records speech without
    requiring speakers, network, or platform TTS. `mode="say"` can use macOS
    `say` for manual local checks.
    """

    mode: str = "dry_run"
    voice: str | None = None
    spoken_texts: list[str] = field(default_factory=list)

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        if not clean_text:
            return TTSResult(ok=False, text=text, engine="local_tts", error="empty text")

        self.spoken_texts.append(clean_text)

        if self.mode == "dry_run":
            return TTSResult(
                ok=True,
                text=clean_text,
                engine="local_tts",
                duration_ms=self._estimate_duration_ms(clean_text),
                metadata={"mode": "dry_run", "tts_call_ms": int((perf_counter() - started) * 1000)},
            )

        if self.mode == "say":
            cmd = ["say"]
            if self.voice:
                cmd.extend(["-v", self.voice])
            cmd.append(clean_text)
            try:
                subprocess.run(cmd, check=True, timeout=60)
                return TTSResult(
                    ok=True,
                    text=clean_text,
                    engine="local_tts",
                    duration_ms=self._estimate_duration_ms(clean_text),
                    metadata={"mode": "say", "voice": self.voice, "tts_call_ms": int((perf_counter() - started) * 1000)},
                )
            except Exception as exc:  # pragma: no cover - platform/manual path
                return TTSResult(ok=False, text=clean_text, engine="local_tts", error=str(exc))

        return TTSResult(ok=False, text=clean_text, engine="local_tts", error=f"unsupported mode: {self.mode}")

    @staticmethod
    def _estimate_duration_ms(text: str) -> int:
        # Rough readable speech estimate for observability only.
        return max(300, int(len(text) / 4 * 1000))
