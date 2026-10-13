"""Research Critic - LLM narrative pass (Section 30/U, ADR-005).

Runs strictly AFTER `services.critic.checklist`'s deterministic pass and
can only ADD objections to the report, never remove or downgrade one the
checklist already raised - enforced here by construction: this function
takes the existing CritiqueReport and returns a new one that is the
checklist's objections plus whatever additional ones the model raises, and
nothing else.
"""

import json
from dataclasses import replace

from app.agents.base import BaseAgent
from app.services.critic.checklist import CritiqueReport, Objection
from app.services.llm.provider import LLMNotConfiguredError

SYSTEM_PROMPT = """You are an adversarial research critic reviewing an experimental design \
summary. You do NOT know whether a deterministic checklist already flagged \
issues - review the design fresh and list any additional methodological \
concerns: confounders, metric choice, statistical methodology, \
overclaiming risk, reproducibility. Do not comment on issues already \
listed as "already flagged" in the input - only add NEW ones.

Return strict JSON: a list of objects with keys "severity" ("blocking", \
"major", or "minor"), "category", and "message". Return an empty list if \
you find nothing beyond what's already flagged."""


class CriticNarrativeAgent(BaseAgent):
    def augment(self, design_summary: str, existing_report: CritiqueReport) -> CritiqueReport:
        if not self.provider.is_configured:
            raise LLMNotConfiguredError(
                "No LLM provider configured; narrative critique cannot run. "
                "The deterministic checklist result is still valid on its own."
            )

        already_flagged = [o.message for o in existing_report.objections]
        prompt = (
            f"Experimental design summary:\n{design_summary}\n\n"
            f"Already flagged (do not repeat these):\n" + "\n".join(f"- {m}" for m in already_flagged)
        )
        response = self.provider.complete(prompt, system=SYSTEM_PROMPT, max_tokens=800)

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = []

        new_objections = []
        for item in parsed if isinstance(parsed, list) else []:
            severity = item.get("severity")
            category = item.get("category")
            message = item.get("message")
            if severity not in ("blocking", "major", "minor") or not category or not message:
                continue
            new_objections.append(Objection(severity=severity, category=f"llm:{category}", message=message))

        return replace(existing_report, objections=[*existing_report.objections, *new_objections])
