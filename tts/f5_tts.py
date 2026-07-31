from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

from .interface import TTSEngine, TTSResult


@dataclass
class F5TTSScriptEngine(TTSEngine):
    """Local F5-TTS engine with a persistent warm worker.

    The previous script path loaded the F5 model on every sentence. This engine
    starts `/Users/admin/Desktop/tmp/f5_worker.py` once per Julia process, keeps
    the model warm, and sends sentence requests over JSONL.
    """

    script_path: Path = Path("/Users/admin/Desktop/tmp/f5_speak.py")
    worker_path: Path = Path("/Users/admin/Desktop/tmp/f5_worker.py")
    timeout_s: float = 300.0
    require_enabled_flag: bool = True
    enabled_flag_path: Path = Path("/tmp/tts_enabled")
    python_bin: str = "/opt/miniconda3/envs/torch_env/bin/python"
    playback: str = "auto"
    _worker: subprocess.Popen | None = field(default=None, init=False, repr=False)
    _worker_ready: dict | None = field(default=None, init=False, repr=False)

    def speak(self, text: str) -> TTSResult:
        started = perf_counter()
        clean_text = text.strip()
        base_metadata = {"worker_path": str(self.worker_path), "python_bin": self.python_bin}
        if not clean_text:
            return self._result(False, text, started, error="empty text", metadata=base_metadata)
        if self.require_enabled_flag and not self.enabled_flag_path.exists():
            return self._result(
                False,
                clean_text,
                started,
                error=f"TTS disabled: {self.enabled_flag_path} not found",
                metadata={**base_metadata, "enabled_flag": str(self.enabled_flag_path)},
            )
        try:
            worker = self._ensure_worker()
            req = {
                "text": clean_text,
                "nfe_step": int(os.environ.get("F5_TTS_NFE_STEP", "16")),
                "speed": float(os.environ.get("F5_TTS_SPEED", "1.0")),
                "ref_audio": os.environ.get("F5_REF_AUDIO", "/Users/admin/Desktop/tmp/word_好爽.wav"),
                "ref_text": os.environ.get("F5_REF_TEXT", "好爽"),
            }
            assert worker.stdin is not None and worker.stdout is not None
            worker.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            worker.stdin.flush()
            line = worker.stdout.readline().strip()
            if not line:
                return self._result(False, clean_text, started, error="F5 worker returned empty response", metadata=base_metadata)
            resp = json.loads(line)
            metadata = {**base_metadata, "worker_ready": self._worker_ready, "worker_response": resp}
            if not resp.get("ok"):
                return self._result(False, clean_text, started, error=resp.get("error", "F5 worker failed"), metadata=metadata)
            audio_path = resp.get("audio_path")
            self._play(audio_path)
            return self._result(True, clean_text, started, metadata={**metadata, "audio_path": audio_path})
        except Exception as exc:  # pragma: no cover - manual adapter path
            self._stop_worker()
            return self._result(False, clean_text, started, error=str(exc), metadata=base_metadata)

    def _ensure_worker(self) -> subprocess.Popen:
        if self._worker and self._worker.poll() is None:
            return self._worker
        python_cmd = self.python_bin or "python3"
        if shutil.which(python_cmd) is None and not Path(python_cmd).exists():
            raise RuntimeError(f"python not found: {python_cmd}")
        if not self.worker_path.exists():
            raise RuntimeError(f"worker not found: {self.worker_path}")
        env = os.environ.copy()
        env.setdefault("F5_TTS_DEVICE", "cpu")
        env.setdefault("F5_TTS_NFE_STEP", "16")
        self._worker = subprocess.Popen(
            [python_cmd, str(self.worker_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        assert self._worker.stdout is not None
        ready_line = self._worker.stdout.readline().strip()
        if not ready_line:
            stderr = self._worker.stderr.read(2000) if self._worker.stderr else ""
            raise RuntimeError(f"F5 worker did not become ready: {stderr}")
        ready = json.loads(ready_line)
        self._worker_ready = ready
        if not ready.get("ready"):
            raise RuntimeError(ready.get("error", "F5 worker not ready"))
        return self._worker

    def _play(self, path: str | None) -> None:
        if not path or os.environ.get("F5_TTS_PLAYER", self.playback) == "none":
            return
        player = os.environ.get("F5_TTS_PLAYER", self.playback)
        if player == "auto":
            if shutil.which("afplay"):
                cmd = ["afplay", path]
            elif shutil.which("ffplay"):
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
            else:
                return
        else:
            cmd = [player, path]
        subprocess.run(cmd, timeout=float(os.environ.get("F5_TTS_PLAY_TIMEOUT", "180")), check=False)

    def _stop_worker(self) -> None:
        worker = self._worker
        if worker and worker.poll() is None:
            try:
                if worker.stdin:
                    worker.stdin.write("__quit__\n")
                    worker.stdin.flush()
                worker.terminate()
                worker.wait(timeout=2)
            except Exception:
                try:
                    worker.kill()
                    worker.wait(timeout=2)
                except Exception:
                    pass
        if worker:
            for stream in (worker.stdin, worker.stdout, worker.stderr):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
        self._worker = None
        self._worker_ready = None

    @staticmethod
    def _result(ok: bool, text: str, started: float, *, error: str | None = None, metadata: dict | None = None) -> TTSResult:
        return TTSResult(
            ok=ok,
            text=text,
            engine="f5_tts_warm_worker",
            error=error,
            metadata={"tts_call_ms": int((perf_counter() - started) * 1000), **(metadata or {})},
        )
