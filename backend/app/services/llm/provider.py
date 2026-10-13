"""LLM provider abstraction (Section 33 / ADR-00X).

Rule 1-4 in practice: if no provider is configured, agents that need LLM
reasoning must fail loudly with LLMNotConfiguredError - never fall back to
fabricated text presented as a real model response.

Every LLM call is logged (model, prompt hash, token usage, latency) so that
"AI-generated" content is always attributable to a specific call, not
invented after the fact.
"""

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


class LLMNotConfiguredError(RuntimeError):
    """Raised instead of returning fabricated output when no LLM provider
    is configured. Callers must surface this to the user, not swallow it."""


@dataclass
class LLMCallRecord:
    model: str
    prompt_hash: str
    system_prompt_hash: Optional[str]
    latency_seconds: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class LLMResponse:
    text: str
    record: LLMCallRecord


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 2000
    ) -> LLMResponse: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...


def _hash(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str], model: str):
        self._api_key = api_key
        self._model = model
        self._client = None
        if api_key:
            import anthropic  # local import: keep the SDK optional at module load time

            self._client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def complete(self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 2000) -> LLMResponse:
        if not self.is_configured:
            raise LLMNotConfiguredError(
                "ANTHROPIC_API_KEY is not set. Refusing to fabricate an LLM response - "
                "configure a provider or mark this research step NOT_IMPLEMENTED."
            )
        start = time.time()
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": self._model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        latency = time.time() - start
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        record = LLMCallRecord(
            model=self._model,
            prompt_hash=_hash(prompt),
            system_prompt_hash=_hash(system),
            latency_seconds=latency,
            input_tokens=getattr(response.usage, "input_tokens", None),
            output_tokens=getattr(response.usage, "output_tokens", None),
        )
        return LLMResponse(text=text, record=record)


class NullProvider(LLMProvider):
    """Explicit "no LLM" provider. Used in tests and when no API key is
    configured. Never returns text - always raises, per Rule 1."""

    @property
    def is_configured(self) -> bool:
        return False

    def complete(self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 2000) -> LLMResponse:
        raise LLMNotConfiguredError(
            "No LLM provider is configured. This step cannot proceed and must "
            "be marked NOT_IMPLEMENTED rather than produce fabricated output."
        )


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
    return NullProvider()
