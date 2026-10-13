import json

import pytest

from app.models.enums import ClaimType
from app.services.literature.claim_extraction import extract_claims
from app.services.llm.provider import LLMCallRecord, LLMNotConfiguredError, LLMProvider, LLMResponse


class FakeProvider(LLMProvider):
    """Test double - returns a fixed JSON payload instead of calling a real
    API, so claim_extraction's parsing/validation logic can be tested
    without network access or an API key."""

    def __init__(self, payload):
        self._payload = payload

    @property
    def is_configured(self) -> bool:
        return True

    def complete(self, prompt, *, system=None, max_tokens=2000):
        return LLMResponse(
            text=json.dumps(self._payload),
            record=LLMCallRecord(model="fake", prompt_hash="x", system_prompt_hash="y", latency_seconds=0.0),
        )


ABSTRACT = "We show that graph-based features improve F1 by 12% over a random-forest baseline on the CIC-IDS2017 dataset."


def test_extract_claims_accepts_grounded_span():
    provider = FakeProvider(
        [
            {
                "claim_text": "Graph features improve F1 by 12%.",
                "source_span": "graph-based features improve F1 by 12%",
            }
        ]
    )
    result = extract_claims(provider, ABSTRACT, model_name="fake-model")
    assert len(result.claims) == 1
    assert result.claims[0]["claim_type"] == ClaimType.AI_INFERRED


def test_extract_claims_rejects_ungrounded_span():
    """Section AB / provenance guard: a claim whose source_span does not
    literally appear in the abstract must be dropped, not accepted on
    the model's say-so."""
    provider = FakeProvider(
        [
            {
                "claim_text": "The moon is made of cheese.",
                "source_span": "this text does not appear in the abstract",
            }
        ]
    )
    result = extract_claims(provider, ABSTRACT, model_name="fake-model")
    assert result.claims == []


def test_extract_claims_handles_malformed_json_gracefully():
    class BrokenProvider(FakeProvider):
        def complete(self, prompt, *, system=None, max_tokens=2000):
            return LLMResponse(
                text="not valid json {{{",
                record=LLMCallRecord(
                    model="fake", prompt_hash="x", system_prompt_hash="y", latency_seconds=0.0
                ),
            )

    result = extract_claims(BrokenProvider([]), ABSTRACT, model_name="fake-model")
    assert result.claims == []


def test_extract_claims_requires_configured_provider():
    from app.services.llm.provider import NullProvider

    with pytest.raises(LLMNotConfiguredError):
        extract_claims(NullProvider(), ABSTRACT, model_name="none")
