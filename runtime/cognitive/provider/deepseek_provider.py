from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from time import perf_counter

from runtime.cognitive.cognitive_context import JuliaContext
from runtime.cognitive.prompt_builder import PromptBuilder
from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from runtime.cognitive.provider.openai_compatible import OpenAICompatibleClient, OpenAICompatibleConfig


@dataclass
class DeepSeekProvider(LLMProvider):
    """Direct DeepSeek API provider consuming JuliaContext.

    The provider does not own Julia identity or memory. It only translates
    JuliaContext into OpenAI-compatible messages and calls DeepSeek.
    """

    api_key: str | None = None
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com/v1"
    timeout_s: float = 60.0
    prompt_builder: PromptBuilder | None = None
    client: OpenAICompatibleClient | None = None
    max_tokens: int | None = None
    temperature: float | None = None

    provider_name: str = "deepseek_provider"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="deepseek",
            model=self.model,
            supports_stream=True,
            supports_tools=False,
            max_context=64000,
            metadata={"api_format": "openai_compatible"},
        )

    def __post_init__(self) -> None:
        if self.prompt_builder is None:
            self.prompt_builder = PromptBuilder()
        key = os.environ.get("DEEPSEEK_API_KEY", "") if self.api_key is None else self.api_key
        self.api_key = key
        if self.client is None and key:
            self.client = OpenAICompatibleClient(
                OpenAICompatibleConfig(
                    base_url=self.base_url,
                    api_key=key,
                    model=self.model,
                    timeout_s=self.timeout_s,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            )

    def build_messages(self, context: JuliaContext) -> list[dict[str, str]]:
        assert self.prompt_builder is not None
        return self.prompt_builder.build(context).to_openai_messages()

    def build_messages_with_timing(self, context: JuliaContext) -> tuple[list[dict[str, str]], dict[str, int]]:
        started = perf_counter()
        messages = self.build_messages(context)
        prompt_built = perf_counter()
        input_chars = sum(len(message.get("content", "")) for message in messages)
        return messages, {
            "prompt_build_ms": int((prompt_built - started) * 1000),
            "prompt_input_chars": input_chars,
            "prompt_message_count": len(messages),
        }

    def _client_options(self) -> dict:
        options = {}
        if self.max_tokens is not None:
            options["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            options["temperature"] = self.temperature
        return options

    def generate(self, context: JuliaContext) -> LLMResponse:
        if self.client is None:
            return LLMResponse(
                text="",
                provider=self.provider_name,
                ok=False,
                error="DEEPSEEK_API_KEY is not configured",
                metadata=self._metadata(context, model=self.model, latency_ms=0, usage=None),
            )
        started = perf_counter()
        try:
            messages, prompt_timing = self.build_messages_with_timing(context)
            result = self.client.chat(messages, **self._client_options())
        except Exception as exc:
            return LLMResponse(
                text="",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
                metadata=self._metadata(context, model=self.model, latency_ms=int((perf_counter() - started) * 1000), usage=None),
            )
        return LLMResponse(
            text=result.text,
            provider=self.provider_name,
            metadata=self._metadata(context, model=result.model, latency_ms=result.latency_ms, usage=result.usage, provider_timing={**prompt_timing, **result.timings}),
        )

    def stream(self, context: JuliaContext) -> Iterator[LLMChunk]:
        if self.client is None:
            yield LLMChunk(
                text="",
                provider=self.provider_name,
                index=0,
                is_final=True,
                ok=False,
                error="DEEPSEEK_API_KEY is not configured",
                metadata=self._metadata(context, model=self.model, latency_ms=0, usage=None),
            )
            return
        started = perf_counter()
        try:
            messages, prompt_timing = self.build_messages_with_timing(context)
            for chunk in self.client.stream_chat(messages, **self._client_options()):
                yield LLMChunk(
                    text=chunk.text,
                    provider=self.provider_name,
                    index=chunk.index,
                    is_final=chunk.is_final,
                    metadata=self._metadata(
                        context,
                        model=chunk.model or self.model,
                        latency_ms=chunk.latency_ms,
                        usage=None,
                        provider_timing={**prompt_timing, **chunk.timings},
                    ),
                )
        except Exception as exc:
            yield LLMChunk(
                text="",
                provider=self.provider_name,
                index=0,
                is_final=True,
                ok=False,
                error=str(exc),
                metadata=self._metadata(context, model=self.model, latency_ms=int((perf_counter() - started) * 1000), usage=None),
            )


    def generate_messages(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Generate from provider-ready messages produced by Phase 3.5 renderer."""
        if self.client is None:
            return LLMResponse(
                text="",
                provider=self.provider_name,
                ok=False,
                error="DEEPSEEK_API_KEY is not configured",
                metadata=self._message_metadata(model=self.model, latency_ms=0, usage=None),
            )
        started = perf_counter()
        try:
            prompt_started = perf_counter()
            input_chars = sum(len(message.get("content", "")) for message in messages)
            prompt_timing = {
                "prompt_build_ms": int((perf_counter() - prompt_started) * 1000),
                "prompt_input_chars": input_chars,
                "prompt_message_count": len(messages),
            }
            result = self.client.chat(messages, **self._client_options())
        except Exception as exc:
            return LLMResponse(
                text="",
                provider=self.provider_name,
                ok=False,
                error=str(exc),
                metadata=self._message_metadata(model=self.model, latency_ms=int((perf_counter() - started) * 1000), usage=None),
            )
        return LLMResponse(
            text=result.text,
            provider=self.provider_name,
            metadata=self._message_metadata(model=result.model, latency_ms=result.latency_ms, usage=result.usage, provider_timing={**prompt_timing, **result.timings}),
        )

    def stream_messages(self, messages: list[dict[str, str]]) -> Iterator[LLMChunk]:
        """Stream from provider-ready messages produced by Phase 3.5 renderer."""
        if self.client is None:
            yield LLMChunk(
                text="",
                provider=self.provider_name,
                index=0,
                is_final=True,
                ok=False,
                error="DEEPSEEK_API_KEY is not configured",
                metadata=self._message_metadata(model=self.model, latency_ms=0, usage=None),
            )
            return
        started = perf_counter()
        try:
            prompt_started = perf_counter()
            input_chars = sum(len(message.get("content", "")) for message in messages)
            prompt_timing = {
                "prompt_build_ms": int((perf_counter() - prompt_started) * 1000),
                "prompt_input_chars": input_chars,
                "prompt_message_count": len(messages),
            }
            for chunk in self.client.stream_chat(messages, **self._client_options()):
                yield LLMChunk(
                    text=chunk.text,
                    provider=self.provider_name,
                    index=chunk.index,
                    is_final=chunk.is_final,
                    metadata=self._message_metadata(
                        model=chunk.model or self.model,
                        latency_ms=chunk.latency_ms,
                        usage=None,
                        provider_timing={**prompt_timing, **chunk.timings},
                    ),
                )
        except Exception as exc:
            yield LLMChunk(
                text="",
                provider=self.provider_name,
                index=0,
                is_final=True,
                ok=False,
                error=str(exc),
                metadata=self._message_metadata(model=self.model, latency_ms=int((perf_counter() - started) * 1000), usage=None),
            )

    def _message_metadata(
        self,
        *,
        model: str,
        latency_ms: int,
        usage: dict | None,
        provider_timing: dict[str, int] | None = None,
    ) -> dict:
        provider_timing = provider_timing or {}
        return {
            "provider": "deepseek",
            "model": model,
            "usage": usage,
            "latency": {"total_ms": latency_ms, **provider_timing},
            "provider_timing": provider_timing,
            "context_runtime_state": {"mode": "conversation", "voice_enabled": True, "current_backend": self.provider_name},
            "provider_info": {
                "name": "deepseek",
                "model": model,
                "supports_stream": True,
                "supports_tools": False,
                "max_context": 64000,
                "metadata": {"api_format": "openai_compatible"},
            },
        }

    @staticmethod
    def _metadata(
        context: JuliaContext,
        *,
        model: str,
        latency_ms: int,
        usage: dict | None,
        provider_timing: dict[str, int] | None = None,
    ) -> dict:
        provider_timing = provider_timing or {}
        return {
            "provider": "deepseek",
            "model": model,
            "usage": usage,
            "latency": {"total_ms": latency_ms, **provider_timing},
            "provider_timing": provider_timing,
            "context_runtime_state": context.runtime_state,
            "provider_info": {
                "name": "deepseek",
                "model": model,
                "supports_stream": True,
                "supports_tools": False,
                "max_context": 64000,
                "metadata": {"api_format": "openai_compatible"},
            },
        }
