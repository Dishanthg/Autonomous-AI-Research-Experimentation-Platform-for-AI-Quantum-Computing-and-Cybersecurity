"""Shared agent scaffolding (Section 31/G).

Every agent in this package:
  - takes an injected LLMProvider (never imports a hardcoded one), so tests
    can pass a FakeProvider double with no network/API key;
  - raises LLMNotConfiguredError (never returns fabricated text) if the
    provider isn't configured - callers must surface this, not swallow it;
  - returns an AgentOutput carrying the provenance record (model, prompt
    hash, latency) alongside the content, so every AI-generated value the
    system displays is traceable to a specific call (Rule 11/ADR-001);
  - is stateless between calls - no shared conversation across agents, so
    one agent's hallucination cannot silently become another agent's
    "established fact" (Section G).
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

from app.services.llm.provider import LLMCallRecord, LLMProvider

T = TypeVar("T")


@dataclass
class AgentOutput(Generic[T]):
    content: T
    record: LLMCallRecord
    claim_type: str = "AI_INFERRED"


class BaseAgent:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    @property
    def is_configured(self) -> bool:
        return self.provider.is_configured
