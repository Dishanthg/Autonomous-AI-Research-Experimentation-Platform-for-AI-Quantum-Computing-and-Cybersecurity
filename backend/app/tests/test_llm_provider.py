import pytest

from app.services.llm.provider import AnthropicProvider, LLMNotConfiguredError, NullProvider, get_llm_provider


def test_null_provider_is_not_configured():
    provider = NullProvider()
    assert provider.is_configured is False


def test_null_provider_raises_instead_of_fabricating():
    provider = NullProvider()
    with pytest.raises(LLMNotConfiguredError):
        provider.complete("draft a hypothesis")


def test_anthropic_provider_without_key_raises_not_fabricates():
    provider = AnthropicProvider(api_key=None, model="claude-sonnet-5")
    assert provider.is_configured is False
    with pytest.raises(LLMNotConfiguredError):
        provider.complete("draft a hypothesis")


def test_get_llm_provider_returns_a_provider_instance():
    provider = get_llm_provider()
    assert hasattr(provider, "is_configured")
    assert hasattr(provider, "complete")
