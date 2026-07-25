from __future__ import annotations

import difflib
import re
from pathlib import Path

from prosebench.document import NumberedDocument
from prosebench.models import (
    AssessmentContext,
    AssessmentResult,
    ClaimAuditItem,
    CoachingPlan,
    ComparisonResult,
    Confidence,
    CriterionAssessment,
    CriterionDelta,
    EvidencePolarity,
    MetricSnapshot,
    RevisionPriority,
    RevisionResult,
)
from prosebench.providers import ProseProvider
from prosebench.rubric import RubricProfile


class AssessmentPipeline:
    def __init__(self, provider: ProseProvider) -> None:
        self.provider = provider

    def assess(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        context: AssessmentContext,
    ) -> AssessmentResult:
        draft = self.provider.assess(document, rubric, context)
        expected = [item.criterion_id for item in rubric.criteria]
        received = [item.criterion_id for item in draft.criteria]
        if len(received) != len(set(received)):
            raise ValueError("Provider returned duplicate criterion IDs.")
        missing = sorted(set(expected) - set(received))
        extra = sorted(set(received) - set(expected))
        if missing or extra:
            raise ValueError(f"Provider criterion mismatch. Missing={missing}; extra={extra}")
        by_id = {item.criterion_id: item for item in draft.criteria}
        criteria: list[CriterionAssessment] = []
        for spec in rubric.criteria:
            item = by_id[spec.criterion_id]
            points = round(spec.weight * item.rating / 4, 2)
            criteria.append(
                CriterionAssessment(
                    criterion_id=spec.criterion_id,
                    label=spec.label,
                    question=spec.question,
                    rating=round(item.rating, 2),
                    weight=spec.weight,
                    points=points,
                    confidence=item.confidence,
                    rationale=item.rationale,
                    evidence=item.evidence,
                    revision_action=item.revision_action,
                )
            )
        warnings = list(draft.warnings)
        confidence = aggregate_confidence([item.confidence for item in criteria])
        if document.stats().word_count < 150:
            warnings.append("The document is short; several criterion judgments may be unstable.")
            confidence = Confidence.LOW
        return AssessmentResult(
            document_name=document.name,
            profile=rubric.name,
            profile_version=rubric.version,
            provider=self.provider.name,
            model=self.provider.model,
            context=context,
            document_stats=document.stats(),
            reader_account=draft.reader_account,
            strengths=draft.strengths,
            priorities=draft.priorities,
            criteria=criteria,
            overall_score=round(sum(item.points for item in criteria), 2),
            overall_confidence=confidence,
            integrity_status=draft.integrity_status,
            integrity_notes=draft.integrity_notes,
            warnings=dedupe(warnings),
        )

    def coach(self, assessment: AssessmentResult, max_priorities: int = 3) -> CoachingPlan:
        ranked = sorted(
            assessment.criteria,
            key=lambda item: ((4 - item.rating) * item.weight, item.weight),
            reverse=True,
        )
        priorities: list[RevisionPriority] = []
        for order, item in enumerate(ranked[:max_priorities], 1):
            limitations = [e for e in item.evidence if e.polarity == EvidencePolarity.LIMITATION]
            why = limitations[0].interpretation if limitations else item.rationale
            priorities.append(
                RevisionPriority(
                    order=order,
                    criterion_id=item.criterion_id,
                    title=item.label,
                    why=why,
                    locations=dedupe([e.location for e in limitations if e.location]),
                    actions=[item.revision_action],
                )
            )
        global_ids = {
            "rhetorical_fit", "motive", "controlling_idea", "development",
            "support", "complexity", "macrostructure",
        }
        defer = []
        if any(item.criterion_id in global_ids for item in priorities):
            defer.append("Delay sentence polishing until purpose, claim, development, support, and sequence are stable.")
        defer.append("Do not rewrite merely to alter punctuation, vocabulary rarity, or sentence-length variation.")
        return CoachingPlan(
            document_name=assessment.document_name,
            profile=assessment.profile,
            reader_experience=assessment.reader_account,
            priorities=priorities,
            defer_until_later=defer,
            warnings=assessment.warnings,
        )

    def revise(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        assessment: AssessmentResult,
        focus: list[str],
        mode: str,
        fact_lock: str,
    ) -> RevisionResult:
        draft = self.provider.revise(document, rubric, assessment, focus, mode, fact_lock)
        rewritten = draft.rewritten_text.strip()
        if not rewritten:
            raise ValueError("Provider returned an empty rewrite.")
        automatic = audit_locked_tokens(document.text, rewritten)
        combined = merge_claim_audits(draft.claim_audit, automatic)
        warnings = list(draft.warnings)
        if any(item.status != "preserved" for item in combined):
            warnings.append("The claim-lock audit found added, removed, changed, or review-needed tokens. Inspect them before accepting the candidate.")
        return RevisionResult(
            document_name=document.name,
            provider=self.provider.name,
            model=self.provider.model,
            profile=rubric.name,
            focus=focus,
            mode=mode,
            fact_lock=fact_lock,
            original_text=document.text,
            rewritten_text=rewritten,
            unified_diff=unified_diff(document.text, rewritten, document.name, f"{Path(document.name).stem}-revised.md"),
            change_log=draft.change_log,
            claim_audit=combined,
            unresolved_issues=draft.unresolved_issues,
            warnings=dedupe(warnings),
        )


def compare_documents(
    before: NumberedDocument,
    after: NumberedDocument,
    before_assessment: AssessmentResult | None = None,
    after_assessment: AssessmentResult | None = None,
) -> ComparisonResult:
    b = before.stats()
    a = after.stats()
    deltas: list[CriterionDelta] = []
    if before_assessment and after_assessment:
        after_by_id = {item.criterion_id: item for item in after_assessment.criteria}
        for before_item in before_assessment.criteria:
            after_item = after_by_id.get(before_item.criterion_id)
            if not after_item:
                continue
            deltas.append(
                CriterionDelta(
                    criterion_id=before_item.criterion_id,
                    label=before_item.label,
                    before_rating=before_item.rating,
                    after_rating=after_item.rating,
                    rating_delta=round(after_item.rating - before_item.rating, 2),
                    before_points=before_item.points,
                    after_points=after_item.points,
                    points_delta=round(after_item.points - before_item.points, 2),
                )
            )
    score_before = before_assessment.overall_score if before_assessment else None
    score_after = after_assessment.overall_score if after_assessment else None
    return ComparisonResult(
        before_name=before.name,
        after_name=after.name,
        before_metrics=MetricSnapshot(
            word_count=b.word_count,
            sentence_count=b.sentence_count,
            paragraph_count=b.paragraph_count,
            average_sentence_words=b.average_sentence_words,
            sentence_length_stdev=b.sentence_length_stdev,
        ),
        after_metrics=MetricSnapshot(
            word_count=a.word_count,
            sentence_count=a.sentence_count,
            paragraph_count=a.paragraph_count,
            average_sentence_words=a.average_sentence_words,
            sentence_length_stdev=a.sentence_length_stdev,
        ),
        word_count_delta=a.word_count - b.word_count,
        sentence_count_delta=a.sentence_count - b.sentence_count,
        paragraph_count_delta=a.paragraph_count - b.paragraph_count,
        unified_diff=unified_diff(before.text, after.text, before.name, after.name),
        score_before=score_before,
        score_after=score_after,
        score_delta=round(score_after - score_before, 2) if score_before is not None and score_after is not None else None,
        criterion_deltas=deltas,
        warnings=(
            ["Score deltas reflect evaluator judgments and rubric fit, not authorship or originality."]
            if before_assessment and after_assessment else []
        ),
    )


def audit_locked_tokens(original: str, revised: str) -> list[ClaimAuditItem]:
    patterns = {
        "number": r"(?<!\w)[+-]?(?:\d+[\d,]*(?:\.\d+)?%?)(?!\w)",
        "url": r"https?://[^\s)>\]]+",
        "citation": r"(?:\[[0-9]+\]|\([A-Z][^()]{0,80}\b(?:19|20)\d{2}[a-z]?\))",
        "quotation": r"[\"“][^\"”\n]{3,}[\"”]",
    }
    audit: list[ClaimAuditItem] = []
    for token_type, pattern in patterns.items():
        before = multiset(re.findall(pattern, original))
        after = multiset(re.findall(pattern, revised))
        for token in sorted(set(before) | set(after)):
            before_count = before.get(token, 0)
            after_count = after.get(token, 0)
            if before_count == after_count:
                status, note = "preserved", f"Present {before_count} time(s) in both versions."
            elif before_count == 0:
                status, note = "added", f"Added {after_count} time(s) in the candidate."
            elif after_count == 0:
                status, note = "removed", f"Removed {before_count} time(s) from the source."
            else:
                status, note = "changed", f"Count changed from {before_count} to {after_count}."
            audit.append(ClaimAuditItem(token_type=token_type, value=token, status=status, note=note))
    return audit


def unified_diff(original: str, revised: str, original_name: str, revised_name: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            original.splitlines(), revised.splitlines(),
            fromfile=original_name, tofile=revised_name, lineterm="",
        )
    )


def aggregate_confidence(values: list[Confidence]) -> Confidence:
    if not values:
        return Confidence.LOW
    scores = {Confidence.LOW: 1, Confidence.MEDIUM: 2, Confidence.HIGH: 3}
    average = sum(scores[value] for value in values) / len(values)
    if average >= 2.5:
        return Confidence.HIGH
    if average >= 1.6:
        return Confidence.MEDIUM
    return Confidence.LOW


def multiset(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = value.strip()
        counts[normalized] = counts.get(normalized, 0) + 1
    return counts


def merge_claim_audits(primary: list[ClaimAuditItem], automatic: list[ClaimAuditItem]) -> list[ClaimAuditItem]:
    merged: dict[tuple[str, str], ClaimAuditItem] = {}
    for item in [*primary, *automatic]:
        key = (item.token_type, item.value)
        existing = merged.get(key)
        if existing is None or existing.status == "preserved":
            merged[key] = item
    return sorted(merged.values(), key=lambda item: (item.token_type, item.value))


def dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
