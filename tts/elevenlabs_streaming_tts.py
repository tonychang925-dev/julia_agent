from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from .interface import TTSEngine, TTSResult


@dataclass
class ElevenLabsStreamingTTSEngine(TTSEngine):
    """Native ElevenLabs streaming playback engine.

    Unlike el_speak.py, this engine does not wait for the full MP3 to download
    into a temp file. It streams HTTP audio chunks directly into ffplay stdin.
    The call still returns after playback finishes, but metadata exposes
    first_byte_ms so we can distinguish network/TTS startup from playback time.
    """

    api_key: str | None = None
    voice_id: str | None = None
    model_id: str | None = None
    output_format: str | None = None
    timeout_s: float = 60.0
    require_enabled_flag: bool = True
    enabled_flag_path: Path = Path("/tmp/tts_enabled")
    base_url: str = "https://api.elevenlabs.io/v1"
    chunk_size: int = 4096

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if self.voice_id is None:
            self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "tOuLUAIdXShmWH7PEUrU")
        if self.model_id is None:
            # Lower-latency default for realtime conversation. Can be overridden
            # without code changes: ELEVENLABS_MODEL_ID=eleven_v3.
            self.model_id = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")
        if self.output_format is None:
            self.output_format = os.environ.get("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        metadata = {
            "voice_id": self.voice_id,
            "model_id": self.model_id,
            "output_format": self.output_format,
            "streaming_playback": True,
        }
        if not clean_text:
            return self._result(False, text, started, error="empty text", metadata=metadata)
        if self.require_enabled_flag and not self.enabled_flag_path.exists():
            return self._result(False, clean_text, started, error=f"TTS disabled: {self.enabled_flag_path} not found", metadata=metadata)
        if not self.api_key:
            return self._result(False, clean_text, started, error="ELEVENLABS_API_KEY is not configured", metadata=metadata)
        if shutil.which("ffplay") is None:
            return self._result(False, clean_text, started, error="ffplay not found in PATH", metadata=metadata)

        url = f"{self.base_url}/text-to-speech/{self.voice_id}/stream?output_format={self.output_format}"
        body = json.dumps(
            {
                "text": clean_text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.3,
                    "similarity_boost": 0.85,
                    "style": 0.1,
                    "use_speaker_boost": False,
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=body)
        req.add_header("xi-api-key", self.api_key)
        req.add_header("Content-Type", "application/json")

        ffplay = None
        first_byte_ms: int | None = None
        audio_bytes = 0
        try:
            ffplay = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", "pipe:0"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                first = resp.read(self.chunk_size)
                if not first:
                    return self._close_with_error(ffplay, clean_text, started, "empty audio response", metadata)
                first_byte_ms = int((perf_counter() - started) * 1000)
                if first[:1] == b"{":
                    error_payload = first + resp.read()
                    try:
                        err = json.loads(error_payload.decode("utf-8", errors="replace"))
                        detail = err.get("detail", {})
                        message = detail.get("message", str(err)) if isinstance(detail, dict) else str(err)
                    except Exception:
                        message = error_payload[:500].decode("utf-8", errors="replace")
                    return self._close_with_error(ffplay, clean_text, started, f"API Error: {message}", {**metadata, "first_byte_ms": first_byte_ms})
                assert ffplay.stdin is not None
                ffplay.stdin.write(first)
                ffplay.stdin.flush()
                audio_bytes += len(first)
                while True:
                    chunk = resp.read(self.chunk_size)
                    if not chunk:
                        break
                    ffplay.stdin.write(chunk)
                    audio_bytes += len(chunk)
                ffplay.stdin.close()
                returncode = ffplay.wait(timeout=self.timeout_s)
                if returncode != 0:
                    stderr = (ffplay.stderr.read() if ffplay.stderr else b"").decode("utf-8", errors="replace")
                    return self._result(False, clean_text, started, error=f"ffplay exited with {returncode}: {stderr[-500:]}", metadata={**metadata, "first_byte_ms": first_byte_ms, "audio_bytes": audio_bytes})
                return self._result(True, clean_text, started, metadata={**metadata, "first_byte_ms": first_byte_ms, "audio_bytes": audio_bytes})
        except Exception as exc:
            if ffplay is not None:
                try:
                    ffplay.kill()
                except Exception:
                    pass
            return self._result(False, clean_text, started, error=str(exc), metadata={**metadata, "first_byte_ms": first_byte_ms, "audio_bytes": audio_bytes})

    def _close_with_error(self, ffplay: subprocess.Popen, text: str, started: float, error: str, metadata: dict) -> TTSResult:
        try:
            if ffplay.stdin:
                ffplay.stdin.close()
            ffplay.kill()
        except Exception:
            pass
        return self._result(False, text, started, error=error, metadata=metadata)

    @staticmethod
    def _result(ok: bool, text: str, started: float, *, error: str | None = None, metadata: dict | None = None) -> TTSResult:
        return TTSResult(
            ok=ok,
            text=text,
            engine="elevenlabs_streaming",
            error=error,
            metadata={"tts_call_ms": int((perf_counter() - started) * 1000), **(metadata or {})},
        )
