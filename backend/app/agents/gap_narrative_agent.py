"""Gap Analyzer - LLM narrative framing (Section 12/L, ADR-007).

Turns a deterministic GapCandidate (from Cypher queries over the knowledge
graph - see `services.knowledge_graph.gap_queries`) into a human-readable
description. This agent NEVER invents the underlying evidence - it only
narrates evidence already produced by the deterministic query. The
confidence score is computed here from the evidence shape, not asserted
freely by the model, and `human_verification_required` is always True
regardless of what the model writes (Section 12's hard requirement).
"""

import json
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.services.knowledge_graph.gap_queries import GapCandidate

SYSTEM_PROMPT = """You write a one-paragraph, plain-language explanation of why a candidate \
research gap might matter, given ONLY the structured evidence provided. Do \
not invent papers, statistics, or evidence not present in the input. If \
the evidence is thin, say so explicitly rather than writing confidently. \
Return strict JSON: {"narrative": string, "confidence_rationale": string}."""


@dataclass
class NarratedGap:
    category: str
    narrative: str
    confidence: float
    confidence_rationale: str
    evidence: dict
    human_verification_required: bool = True


def compute_confidence(candidate: GapCandidate) -> float:
    """Deterministic confidence heuristic from the evidence shape itself -
    not something the LLM is trusted to self-report."""
    paper_count = candidate.evidence.get("paper_count")
    if paper_count is not None:
        return max(0.1, min(0.9, 1.0 - (paper_count / 5)))
    return 0.3  # missing-baseline candidates: fixed low-moderate default


class GapNarrativeAgent(BaseAgent):
    def narrate(self, candidate: GapCandidate) -> NarratedGap:
        prompt = f"Gap category: {candidate.category}\nStructural description: {candidate.description}\nEvidence: {json.dumps(candidate.evidence)}"
        response = self.provider.complete(prompt, system=SYSTEM_PROMPT, max_tokens=400)

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = {}

        return NarratedGap(
            category=candidate.category,
            narrative=parsed.get("narrative", candidate.description),
            confidence=compute_confidence(candidate),
            confidence_rationale=parsed.get("confidence_rationale", "derived from evidence paper_count"),
            evidence=candidate.evidence,
            human_verification_required=True,
        )
