from __future__ import annotations

from collections.abc import Iterator

from runtime.cognitive.cognitive_context import JuliaContext
from runtime.cognitive.provider.capability import ProviderInfo
from runtime.cognitive.provider.llm_provider import LLMChunk, LLMProvider, LLMResponse
from tts.chunking import split_for_tts


class EchoProvider(LLMProvider):
    """Provider-independent test backend for JuliaContext validation."""

    provider_name = "echo_provider"

    def info(self) -> ProviderInfo:
        return ProviderInfo(name="echo", model="echo-v0", supports_stream=True, supports_tools=False, max_context=None)

    def generate(self, context: JuliaContext) -> LLMResponse:
        identity_yaml = context.identity.get("yaml", {})
        name = identity_yaml.get("identity", {}).get("name", "Julia") if isinstance(identity_yaml, dict) else "Julia"
        user = context.relationship.get("user", {}).get("name", "Tony") if isinstance(context.relationship, dict) else "Tony"
        if context.policy.get("response_mode") == "vocal_gesture_generation":
            text = f"嗯……啊……{user}。"
        elif "你是谁" in context.current_input:
            text = f"我是{name}，{user}，我由 Julia Runtime 的身份、记忆和对话上下文构成。"
        elif "记得我" in context.current_input:
            text = f"记得，{user}。我会通过 Runtime 加载的记忆和关系上下文保持连续性。"
        else:
            text = f"{user}，我收到了：{context.current_input}"
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            metadata={"identity_name": name, "user_name": user, "context_runtime_state": context.runtime_state, "provider_info": self.info().to_dict()},
        )

    def stream(self, context: JuliaContext) -> Iterator[LLMChunk]:
        response = self.generate(context)
        # EchoProvider is a provider-contract test backend; preserve exact
        # response text across stream join instead of applying TTS sanitization.
        chunks = [response.text]
        for index, chunk in enumerate(chunks):
            yield LLMChunk(
                text=chunk,
                provider=self.provider_name,
                index=index,
                is_final=index == len(chunks) - 1,
                metadata={**response.metadata, "streaming": True, "chunk_count": len(chunks)},
            )
