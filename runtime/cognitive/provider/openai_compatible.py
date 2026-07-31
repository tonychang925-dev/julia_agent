from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 60.0
    max_tokens: int | None = None
    temperature: float | None = None


@dataclass(frozen=True)
class OpenAICompatibleResult:
    text: str
    model: str
    usage: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    timings: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class OpenAICompatibleChunk:
    text: str
    index: int
    is_final: bool = False
    model: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    timings: dict[str, int] = field(default_factory=dict)


class OpenAICompatibleClient:
    """Tiny dependency-free OpenAI-compatible chat completions client."""

    def __init__(self, config: OpenAICompatibleConfig):
        self.config = config

    def chat(self, messages: list[dict[str, str]], *, stream: bool = False, max_tokens: int | None = None, temperature: float | None = None) -> OpenAICompatibleResult:
        if stream:
            raise ValueError("chat(stream=True) is not supported; use stream_chat")
        started = perf_counter()
        payload = self._payload(messages, stream=False, max_tokens=max_tokens, temperature=temperature)
        request_started = perf_counter()
        data = self._post_json(payload)
        response_received = perf_counter()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = str(message.get("content") or "")
        return OpenAICompatibleResult(
            text=text,
            model=str(data.get("model") or self.config.model),
            usage=data.get("usage") if isinstance(data.get("usage"), dict) else None,
            raw=data,
            latency_ms=int((perf_counter() - started) * 1000),
            timings={
                "http_request_total_ms": int((response_received - request_started) * 1000),
                "provider_total_ms": int((perf_counter() - started) * 1000),
            },
        )

    def stream_chat(self, messages: list[dict[str, str]], *, max_tokens: int | None = None, temperature: float | None = None) -> Iterator[OpenAICompatibleChunk]:
        started = perf_counter()
        payload = self._payload(messages, stream=True, max_tokens=max_tokens, temperature=temperature)
        req = self._request(payload)
        request_started = perf_counter()
        try:
            with urlopen(req, timeout=self.config.timeout_s) as response:  # nosec - user-configured API endpoint
                response_opened = perf_counter()
                index = 0
                first_token_at: float | None = None
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        now = perf_counter()
                        yield OpenAICompatibleChunk(
                            text="",
                            index=index,
                            is_final=True,
                            latency_ms=int((now - started) * 1000),
                            timings={
                                "http_response_open_ms": int((response_opened - request_started) * 1000),
                                "provider_first_token_ms": int((first_token_at - started) * 1000) if first_token_at is not None else int((now - started) * 1000),
                                "provider_chunk_ms": int((now - started) * 1000),
                                "provider_total_ms": int((now - started) * 1000),
                            },
                        )
                        return
                    payload = json.loads(data)
                    choice = (payload.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    text = str(delta.get("content") or "")
                    finish_reason = choice.get("finish_reason")
                    if text or finish_reason:
                        now = perf_counter()
                        if text and first_token_at is None:
                            first_token_at = now
                        yield OpenAICompatibleChunk(
                            text=text,
                            index=index,
                            is_final=finish_reason is not None,
                            model=str(payload.get("model") or self.config.model),
                            raw=payload,
                            latency_ms=int((now - started) * 1000),
                            timings={
                                "http_response_open_ms": int((response_opened - request_started) * 1000),
                                "provider_first_token_ms": int((first_token_at - started) * 1000) if first_token_at is not None else int((now - started) * 1000),
                                "provider_chunk_ms": int((now - started) * 1000),
                            },
                        )
                        index += 1
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"OpenAI-compatible stream request failed: {exc}") from exc

    def _payload(self, messages: list[dict[str, str]], *, stream: bool, max_tokens: int | None = None, temperature: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
        }
        resolved_max_tokens = self.config.max_tokens if max_tokens is None else max_tokens
        resolved_temperature = self.config.temperature if temperature is None else temperature
        if resolved_max_tokens is not None:
            payload["max_tokens"] = resolved_max_tokens
        if resolved_temperature is not None:
            payload["temperature"] = resolved_temperature
        return payload

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        req = self._request(payload)
        try:
            with urlopen(req, timeout=self.config.timeout_s) as response:  # nosec - user-configured API endpoint
                body = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc
        data = json.loads(body)
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI-compatible response must be a JSON object")
        return data

    def _request(self, payload: dict[str, Any]) -> Request:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.config.api_key}")
        return req
