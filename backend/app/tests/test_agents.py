"""Tests for the LLM agent layer (app/agents/). All exercised against a
FakeProvider test double - no network access or API key required - so
these tests verify the agents' parsing/validation/safety logic
independently of whether a real LLM is configured (see
docs/architecture/adr for why: ANTHROPIC_API_KEY was not available in this
build environment)."""

import json

import pytest

from app.agents.critic_narrative_agent import CriticNarrativeAgent
from app.agents.gap_narrative_agent import GapNarrativeAgent
from app.agents.hypothesis_agent import HypothesisAgent, InvalidHypothesisDraftError
from app.agents.research_synthesizer_agent import ResearchSynthesizerAgent, check_numeric_consistency
from app.services.critic.checklist import CritiqueReport, Objection
from app.services.knowledge_graph.gap_queries import GapCandidate
from app.services.llm.provider import LLMCallRecord, LLMNotConfiguredError, LLMProvider, LLMResponse


class FakeProvider(LLMProvider):
    def __init__(self, payload):
        self._payload = payload

    @property
    def is_configured(self) -> bool:
        return True

    def complete(self, prompt, *, system=None, max_tokens=2000):
        text = self._payload if isinstance(self._payload, str) else json.dumps(self._payload)
        return LLMResponse(
            text=text,
            record=LLMCallRecord(model="fake", prompt_hash="x", system_prompt_hash="y", latency_seconds=0.0),
        )


# ---- HypothesisAgent ----

VALID_AI_DRAFT = {
    "null_hypothesis": "H0",
    "alternative_hypothesis": "H1",
    "baseline": "logistic_regression",
    "proposed": "random_forest",
    "dataset": "breast_cancer",
    "evaluation_metric": "f1",
    "potential_confounders": ["class_imbalance"],
    "min_effect_size": 0.2,
    "direction": "greater",
}


def test_hypothesis_agent_accepts_valid_draft():
    agent = HypothesisAgent(FakeProvider(VALID_AI_DRAFT))
    result = agent.draft("AI", "Does random forest outperform logistic regression?")
    assert result.content.baseline == "logistic_regression"
    assert result.claim_type == "HYPOTHESIZED"


def test_hypothesis_agent_rejects_out_of_vocabulary_baseline():
    bad = {**VALID_AI_DRAFT, "baseline": "made_up_model"}
    agent = HypothesisAgent(FakeProvider(bad))
    with pytest.raises(InvalidHypothesisDraftError):
        agent.draft("AI", "some question")


def test_hypothesis_agent_rejects_zero_min_effect_size():
    bad = {**VALID_AI_DRAFT, "min_effect_size": 0.0}
    agent = HypothesisAgent(FakeProvider(bad))
    with pytest.raises(InvalidHypothesisDraftError):
        agent.draft("AI", "some question")


def test_hypothesis_agent_rejects_malformed_json():
    agent = HypothesisAgent(FakeProvider("not json {{"))
    with pytest.raises(InvalidHypothesisDraftError):
        agent.draft("AI", "some question")


def test_hypothesis_agent_unknown_domain_raises():
    agent = HypothesisAgent(FakeProvider(VALID_AI_DRAFT))
    with pytest.raises(ValueError):
        agent.draft("NOT_A_DOMAIN", "some question")


# ---- CriticNarrativeAgent ----


def test_critic_narrative_agent_only_adds_objections():
    existing = CritiqueReport(objections=[Objection("blocking", "dataset_quality", "No dataset specified.")])
    new_objection_payload = [
        {"severity": "major", "category": "confounders", "message": "Seasonality not considered."}
    ]
    agent = CriticNarrativeAgent(FakeProvider(new_objection_payload))

    augmented = agent.augment("some design summary", existing)

    assert len(augmented.objections) == 2
    assert augmented.objections[0].message == "No dataset specified."  # original preserved
    assert augmented.objections[1].category == "llm:confounders"


def test_critic_narrative_agent_ignores_malformed_entries():
    agent = CriticNarrativeAgent(
        FakeProvider([{"severity": "not_a_real_severity", "category": "x", "message": "y"}])
    )
    existing = CritiqueReport(objections=[])
    augmented = agent.augment("summary", existing)
    assert augmented.objections == []


def test_critic_narrative_agent_requires_configured_provider():
    from app.services.llm.provider import NullProvider

    agent = CriticNarrativeAgent(NullProvider())
    with pytest.raises(LLMNotConfiguredError):
        agent.augment("summary", CritiqueReport(objections=[]))


# ---- GapNarrativeAgent ----


def test_gap_narrative_agent_preserves_evidence_and_forces_verification():
    candidate = GapCandidate(
        category="unexplored_combination_of_methods",
        description="Method X has only 1 paper on dataset Y.",
        evidence={"method": "X", "dataset": "Y", "paper_count": 1},
    )
    agent = GapNarrativeAgent(
        FakeProvider(
            {"narrative": "This combination is under-studied.", "confidence_rationale": "low paper count"}
        )
    )
    result = agent.narrate(candidate)

    assert result.human_verification_required is True
    assert result.evidence == candidate.evidence
    assert 0.0 < result.confidence <= 0.9


def test_gap_narrative_agent_confidence_is_deterministic_not_llm_reported():
    candidate = GapCandidate(
        category="missing_baseline", description="x", evidence={"method_a": "A", "method_b": "B"}
    )
    # Even if the model tried to report a confidence, the agent computes its
    # own from the evidence shape - there's no "confidence" key path here.
    agent = GapNarrativeAgent(FakeProvider({"narrative": "n/a", "confidence_rationale": "n/a"}))
    result = agent.narrate(candidate)
    assert result.confidence == 0.3  # fixed default for missing-baseline shape


# ---- ResearchSynthesizerAgent ----


def test_synthesizer_flags_invented_number():
    facts = {"f1_mean": 0.87, "p_value": 0.001}
    agent = ResearchSynthesizerAgent(
        FakeProvider({"narrative": "The method achieved 99.9% accuracy, far exceeding expectations."})
    )
    result = agent.synthesize_section("results", facts)
    assert result.numeric_consistency_ok is False
    assert "99.9%" in result.flagged_numbers


def test_synthesizer_accepts_narrative_using_only_given_facts():
    facts = {"f1_mean": 0.87, "p_value": 0.001}
    agent = ResearchSynthesizerAgent(
        FakeProvider({"narrative": "The proposed method achieved a mean F1 of 0.87 (p=0.001)."})
    )
    result = agent.synthesize_section("results", facts)
    assert result.numeric_consistency_ok is True
    assert result.flagged_numbers == []


def test_check_numeric_consistency_tolerates_small_prose_integers():
    ok, flagged = check_numeric_consistency("This was the second experiment in a series of 3.", {"f1": 0.9})
    assert ok is True
    assert flagged == []
