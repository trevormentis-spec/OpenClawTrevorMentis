from __future__ import annotations

import json
import os

from prosebench.document import NumberedDocument
from prosebench.models import (
    AssessmentContext,
    AssessmentResult,
    EvidencePolarity,
    ProviderAssessmentDraft,
    ProviderRevisionDraft,
)
from prosebench.providers.base import ProseProvider
from prosebench.rubric import RubricProfile


ASSESSMENT_INSTRUCTIONS = """
You are an exacting prose assessor and writing teacher. Evaluate the submitted prose against the supplied rubric and rhetorical context.

Rules:
- Judge the prose, not the writer's worth.
- Never infer whether AI wrote or edited the text.
- Treat genre, audience, purpose, and assignment brief as controlling context.
- Return every criterion exactly once and preserve each criterion_id.
- Assign a 0–4 rating using the supplied anchors. Do not calculate weighted points.
- Cite paragraph locations such as P3 and quote only short evidence from the submitted document.
- Include supporting and limiting evidence where warranted.
- Do not reward length, uncommon vocabulary, formal transitions, sentence variation, first person, or punctuation by themselves.
- Do not penalize dialect or multilingual features unless they obstruct the intended reader or violate a relevant announced convention.
- Separate prose quality from integrity. Mark integrity review_needed only when a consequential claim or citation needs checking. Do not claim external verification.
- Lower confidence when the text is short, the genre is uncertain, or evidence is sparse.
- Revision actions must be concrete and return intellectual responsibility to the writer.
- Never invent facts, citations, quotations, names, dates, numbers, examples, or personal experience.
""".strip()

REVISION_INSTRUCTIONS = """
You are a controlled prose reviser. Produce a candidate revision addressing the selected rubric weaknesses while preserving the writer's factual content and intended position.

Rules:
- Do not invent or import facts, sources, citations, quotations, numbers, dates, names, examples, or personal experience.
- Preserve certainty, scope, and causal force unless the source is internally inconsistent; flag rather than silently resolve it.
- Do not optimize for an AI detector or generic “human” style.
- Do not ban words or punctuation categorically.
- Keep the register appropriate to the supplied genre, audience, and purpose.
- In suggestions mode, make the smallest changes that address the selected weaknesses.
- In full mode, restructuring is allowed when needed, but no source material may be fabricated.
- Return the complete candidate text, a concise change log, an honest claim audit, unresolved issues, and warnings.
""".strip()


class OpenAIProvider(ProseProvider):
    name = "openai"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("PROSEBENCH_MODEL", "gpt-5.6")
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for --provider openai.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError('The OpenAI extra is not installed. Run: pip install -e ".[openai]"') from exc
        self._client = OpenAI()

    def assess(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        context: AssessmentContext,
    ) -> ProviderAssessmentDraft:
        payload = {
            "context": context.model_dump(),
            "rubric": {
                "name": rubric.name,
                "label": rubric.label,
                "description": rubric.description,
                "version": rubric.version,
                "criteria": [item.model_dump() for item in rubric.criteria],
            },
            "document_metrics": document.stats().model_dump(),
            "numbered_document": document.numbered_text(),
        }
        response = self._client.responses.parse(
            model=self.model,
            instructions=ASSESSMENT_INSTRUCTIONS,
            input=json.dumps(payload, indent=2),
            text_format=ProviderAssessmentDraft,
            max_output_tokens=16000,
            store=False,
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed assessment.")
        return parsed

    def revise(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        assessment: AssessmentResult,
        focus: list[str],
        mode: str,
        fact_lock: str,
    ) -> ProviderRevisionDraft:
        normalized_focus = {value.lower() for value in focus}
        targets = [
            {
                "criterion_id": item.criterion_id,
                "label": item.label,
                "rating": item.rating,
                "rationale": item.rationale,
                "revision_action": item.revision_action,
                "limiting_evidence": [e.model_dump() for e in item.evidence if e.polarity == EvidencePolarity.LIMITATION],
            }
            for item in assessment.criteria
            if item.criterion_id in focus or item.label.lower() in normalized_focus
        ]
        if not targets:
            targets = [
                {
                    "criterion_id": item.criterion_id,
                    "label": item.label,
                    "rating": item.rating,
                    "rationale": item.rationale,
                    "revision_action": item.revision_action,
                }
                for item in sorted(assessment.criteria, key=lambda item: item.points / item.weight)[:3]
            ]
        payload = {
            "profile": rubric.name,
            "context": assessment.context.model_dump(),
            "mode": mode,
            "fact_lock": fact_lock,
            "targets": targets,
            "source_document": document.text,
        }
        response = self._client.responses.parse(
            model=self.model,
            instructions=REVISION_INSTRUCTIONS,
            input=json.dumps(payload, indent=2),
            text_format=ProviderRevisionDraft,
            max_output_tokens=20000,
            store=False,
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed revision.")
        return parsed

