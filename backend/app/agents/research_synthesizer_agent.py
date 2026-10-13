"""Research Synthesizer (Section 31/73/74). Drafts prose for a research
report section from a fixed set of DB-sourced facts ONLY - never given
open-ended access to invent results, datasets, or statistical values
(Section 74's paper-generation-safety rule).

The underlying numeric facts (metrics, p-values, conclusion status) always
come from and remain owned by the deterministic Result/StatisticalTest
rows - this agent's prose is decoration around them, not a replacement for
them, and the report template renders both: the real numbers from the DB,
and this agent's narrative labeled AI_INFERRED alongside them.

Best-effort safeguard: `check_numeric_consistency` extracts every
standalone number the model wrote and flags any that doesn't appear
(as a substring) among the facts it was given - this cannot prove the
prose is faithful, but it can catch an obviously invented figure.
"""

import json
import re
from dataclasses import dataclass

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You write the prose narrative for one section of a scientific research \
report, using ONLY the facts given to you in the input JSON. Do not invent \
any number, dataset name, paper citation, or claim not present in that \
JSON. If a fact is missing, write "not available" rather than guessing. \
Every specific number in your prose must come directly from the input.

Return strict JSON: {"narrative": string}."""


@dataclass
class SynthesisResult:
    narrative: str
    numeric_consistency_ok: bool
    flagged_numbers: list[str]


def _extract_numbers(text: str) -> list[str]:
    # Decimal point must be followed by a digit to count, so a
    # sentence-ending period after an integer (e.g. "a series of 3.") is
    # not swept into the match as a bogus "3." token.
    return re.findall(r"-?\d+(?:\.\d+)?%?", text)


def _all_fact_strings(facts: dict) -> str:
    return json.dumps(facts, default=str)


def check_numeric_consistency(narrative: str, facts: dict) -> tuple[bool, list[str]]:
    fact_blob = _all_fact_strings(facts)
    flagged = []
    for num in _extract_numbers(narrative):
        bare = num.rstrip("%")
        if bare and bare not in fact_blob and num not in fact_blob:
            # Tolerate small integers (0-12ish) that plausibly appear as
            # prose (e.g. "the third experiment") rather than data.
            try:
                if abs(float(bare)) <= 12 and "." not in bare:
                    continue
            except ValueError:
                pass
            flagged.append(num)
    return (len(flagged) == 0, flagged)


class ResearchSynthesizerAgent(BaseAgent):
    def synthesize_section(self, section_name: str, facts: dict) -> SynthesisResult:
        prompt = f"Section: {section_name}\nFacts (JSON):\n{json.dumps(facts, indent=2, default=str)}"
        response = self.provider.complete(prompt, system=SYSTEM_PROMPT, max_tokens=1000)

        try:
            parsed = json.loads(response.text)
            narrative = parsed.get("narrative", "")
        except json.JSONDecodeError:
            narrative = response.text

        ok, flagged = check_numeric_consistency(narrative, facts)
        return SynthesisResult(narrative=narrative, numeric_consistency_ok=ok, flagged_numbers=flagged)
