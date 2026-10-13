"""Hypothesis Agent (Section 13/G). Drafts a candidate hypothesis from a
research question - output is ALWAYS a DRAFT that must still pass the
deterministic Hypothesis Quality Check (Section 14) and Research Critic
(Section 30) before it can be approved; this agent has no authority to
approve its own output.

Selects baseline/proposed method names ONLY from the fixed, reviewed
vocabulary the codegen templates actually support (Section 16) - the model
is instructed to pick from that list, and the parser rejects any value
outside it rather than trusting the model's choice blindly.
"""

import json
from dataclasses import dataclass

from app.agents.base import AgentOutput, BaseAgent
from app.services.codegen.ai_templates import SUPPORTED_BASELINES, SUPPORTED_DATASETS, SUPPORTED_PROPOSED
from app.services.codegen.cyber_templates import SUPPORTED_DETECTORS

ALLOWED_METHODS = {
    "AI": {
        "baselines": sorted(SUPPORTED_BASELINES),
        "proposed": sorted(SUPPORTED_PROPOSED),
        "datasets": sorted(SUPPORTED_DATASETS),
    },
    "CYBERSECURITY": {
        "baselines": sorted(SUPPORTED_DETECTORS),
        "proposed": sorted(SUPPORTED_DETECTORS),
        "datasets": ["synthetic_traffic_v1"],
    },
}

SYSTEM_PROMPT_TEMPLATE = """You are a research hypothesis drafting assistant for a scientific research \
platform. You draft candidate hypotheses; you never approve them - a \
separate deterministic quality check and critic will review your draft \
before any experiment can run on it.

You must choose "baseline" and "proposed" ONLY from this exact list: {methods}
You must choose "dataset" ONLY from this exact list: {datasets}
Choosing anything outside these lists will cause your draft to be rejected.

Return strict JSON with keys: null_hypothesis (string), alternative_hypothesis \
(string), baseline (string, from the list), proposed (string, from the list), \
dataset (string, from the list), evaluation_metric (string, e.g. "f1"), \
potential_confounders (list of strings), min_effect_size (float, must be > 0), \
direction ("greater", "less", or "any")."""


@dataclass
class HypothesisDraft:
    null_hypothesis: str
    alternative_hypothesis: str
    baseline: str
    proposed: str
    dataset: str
    evaluation_metric: str
    potential_confounders: list[str]
    min_effect_size: float
    direction: str


class InvalidHypothesisDraftError(ValueError):
    """Raised when the model's draft uses a baseline/proposed/dataset name
    outside the fixed vocabulary, or otherwise fails basic structural
    validation - never silently coerced into something plausible-looking."""


class HypothesisAgent(BaseAgent):
    def draft(self, domain: str, research_question: str) -> AgentOutput[HypothesisDraft]:
        allowed = ALLOWED_METHODS.get(domain)
        if allowed is None:
            raise ValueError(f"No method vocabulary registered for domain '{domain}'")

        methods = sorted(set(allowed["baselines"]) | set(allowed["proposed"]))
        system = SYSTEM_PROMPT_TEMPLATE.format(methods=methods, datasets=allowed["datasets"])
        response = self.provider.complete(
            f"Research question: {research_question}\nDomain: {domain}", system=system, max_tokens=800
        )

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise InvalidHypothesisDraftError(f"Model did not return valid JSON: {exc}") from exc

        baseline = parsed.get("baseline")
        proposed = parsed.get("proposed")
        dataset = parsed.get("dataset")
        if baseline not in allowed["baselines"]:
            raise InvalidHypothesisDraftError(
                f"baseline '{baseline}' is not in the allowed vocabulary {allowed['baselines']}"
            )
        if proposed not in allowed["proposed"]:
            raise InvalidHypothesisDraftError(
                f"proposed '{proposed}' is not in the allowed vocabulary {allowed['proposed']}"
            )
        if dataset not in allowed["datasets"]:
            raise InvalidHypothesisDraftError(
                f"dataset '{dataset}' is not in the allowed vocabulary {allowed['datasets']}"
            )

        min_effect_size = float(parsed.get("min_effect_size", 0))
        if min_effect_size <= 0:
            raise InvalidHypothesisDraftError(
                "min_effect_size must be > 0 (a zero threshold would be rejected by the "
                "Research Critic anyway - see ADR-005 - so reject it here instead of "
                "wasting a pipeline stage)."
            )

        draft = HypothesisDraft(
            null_hypothesis=parsed["null_hypothesis"],
            alternative_hypothesis=parsed["alternative_hypothesis"],
            baseline=baseline,
            proposed=proposed,
            dataset=dataset,
            evaluation_metric=parsed.get("evaluation_metric", "f1"),
            potential_confounders=parsed.get("potential_confounders", []),
            min_effect_size=min_effect_size,
            direction=parsed.get("direction", "greater"),
        )
        return AgentOutput(content=draft, record=response.record, claim_type="HYPOTHESIZED")
