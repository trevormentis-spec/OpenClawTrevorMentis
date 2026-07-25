from __future__ import annotations

import re

from prosebench.document import NumberedDocument, words_in
from prosebench.models import (
    AssessmentContext,
    AssessmentResult,
    ChangeLogItem,
    Confidence,
    CriterionDraft,
    EvidenceItem,
    EvidencePolarity,
    IntegrityStatus,
    ProviderAssessmentDraft,
    ProviderRevisionDraft,
)
from prosebench.providers.base import ProseProvider
from prosebench.rubric import CriterionSpec, RubricProfile


class LocalDiagnosticProvider(ProseProvider):
    """Low-confidence, deterministic surface diagnostics for offline use."""

    name = "local"
    model = "deterministic-surface-diagnostics-v1"

    def assess(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        context: AssessmentContext,
    ) -> ProviderAssessmentDraft:
        stats = document.stats()
        text_lower = document.text.lower()
        prose_paragraphs = [p for p in document.paragraphs if not re.fullmatch(r"#{1,6}\s+.+", p.text)]
        opening = prose_paragraphs[0] if prose_paragraphs else document.paragraphs[0]
        representative = max(prose_paragraphs or document.paragraphs, key=lambda p: len(words_in(p.text)))
        first_two = " ".join(p.text for p in prose_paragraphs[:2]).lower()

        signals = {
            "motive": len(re.findall(r"\b(?:problem|question|tension|puzzle|risk|need|conflict|decision|why|how)\b", first_two)),
            "reasoning": len(re.findall(r"\b(?:because|therefore|however|although|while|which means|suggests|implies|so that)\b", text_lower)),
            "counter": len(re.findall(r"\b(?:however|although|while|but|limitation|objection|counterargument|yet|unless|except)\b", text_lower)),
            "examples": len(re.findall(r"\b(?:for example|for instance|consider|such as)\b", text_lower)),
            "filler": len(re.findall(r"\b(?:in order to|due to the fact that|it is important to note that|at this point in time|has the ability to)\b", text_lower)),
            "generic": len(re.findall(r"\b(?:important|significant|crucial|pivotal|plays a key role|modern landscape|robust framework)\b", text_lower)),
        }
        paragraph_lengths = [len(words_in(p.text)) for p in prose_paragraphs]
        multi_sentence = sum(1 for p in prose_paragraphs if len(re.split(r"(?<=[.!?])\s+", p.text)) >= 2)
        support_markers = stats.citation_count + stats.quotation_count + stats.number_count + signals["examples"]

        drafts: list[CriterionDraft] = []
        for spec in rubric.criteria:
            rating, rationale, action, location, interpretation, polarity = self._criterion_signal(
                spec=spec,
                document=document,
                context=context,
                opening=opening.location,
                representative=representative.location,
                signals=signals,
                support_markers=support_markers,
                paragraph_lengths=paragraph_lengths,
                multi_sentence=multi_sentence,
            )
            drafts.append(
                CriterionDraft(
                    criterion_id=spec.criterion_id,
                    rating=round(max(0.0, min(4.0, rating)), 2),
                    confidence=Confidence.LOW,
                    rationale=rationale,
                    evidence=[
                        EvidenceItem(
                            location=location,
                            excerpt=document.excerpt(location) if location.startswith("P") else "",
                            interpretation=interpretation,
                            polarity=polarity,
                        )
                    ],
                    revision_action=action,
                )
            )

        strongest = sorted(drafts, key=lambda item: item.rating, reverse=True)[:2]
        weakest = sorted(drafts, key=lambda item: item.rating)[:3]
        label_by_id = {item.criterion_id: item.label for item in rubric.criteria}
        return ProviderAssessmentDraft(
            reader_account=(
                f"The document contains {stats.word_count} words in {stats.paragraph_count} blocks. "
                "This offline pass identifies surface and document-shape signals only; substantive reasoning and literary quality require a model or trained human reader."
            ),
            strengths=[f"{label_by_id[item.criterion_id]} is comparatively stronger in the offline diagnostic." for item in strongest],
            priorities=[f"Revisit {label_by_id[item.criterion_id].lower()}: {item.revision_action}" for item in weakest],
            criteria=drafts,
            integrity_status=IntegrityStatus.NOT_CHECKED,
            integrity_notes=["Offline mode did not retrieve or verify external sources."],
            warnings=[
                "Offline mode is explicitly low confidence. Its metrics are prompts for inspection, not proof of quality or authorship."
            ],
        )

    def revise(
        self,
        document: NumberedDocument,
        rubric: RubricProfile,
        assessment: AssessmentResult,
        focus: list[str],
        mode: str,
        fact_lock: str,
    ) -> ProviderRevisionDraft:
        replacements = [
            (r"\b[Ii]n order to\b", "To", "Remove a verbose wrapper around an infinitive."),
            (r"\b[Dd]ue to the fact that\b", "Because", "Replace a nominalized causal phrase with a direct conjunction."),
            (r"\b[Aa]t this point in time\b", "Now", "Use the direct time word."),
            (r"\b[Ii]t is important to note that\s*", "", "Remove an announcement and state the claim directly."),
            (r"\bhas the ability to\b", "can", "Use the direct modal verb."),
            (r"\bmake a decision\b", "decide", "Use the direct verb."),
        ]
        rewritten = document.text
        changes: list[ChangeLogItem] = []
        for pattern, replacement, reason in replacements:
            matches = list(re.finditer(pattern, rewritten))
            if not matches:
                continue
            before = matches[0].group(0)
            rewritten, count = re.subn(pattern, replacement, rewritten)
            changes.append(
                ChangeLogItem(
                    criterion_ids=["diction", "sentence_craft"],
                    before=before,
                    after=replacement,
                    reason=f"{reason} Applied {count} time(s).",
                )
            )
        rewritten = re.sub(r"[ \t]+\n", "\n", rewritten)
        rewritten = re.sub(r" {2,}", " ", rewritten)
        warnings = [
            "Offline revision applies only conservative mechanical edits. It does not attempt substantive restructuring."
        ]
        if not changes:
            warnings.append("No conservative local rewrite was available; the candidate matches the source.")
        return ProviderRevisionDraft(
            rewritten_text=rewritten,
            change_log=changes,
            unresolved_issues=assessment.priorities[:3],
            warnings=warnings,
        )

    def _criterion_signal(
        self,
        *,
        spec: CriterionSpec,
        document: NumberedDocument,
        context: AssessmentContext,
        opening: str,
        representative: str,
        signals: dict[str, int],
        support_markers: int,
        paragraph_lengths: list[int],
        multi_sentence: int,
    ) -> tuple[float, str, str, str, str, EvidencePolarity]:
        stats = document.stats()
        criterion = spec.criterion_id
        if criterion == "rhetorical_fit":
            rating = 2.0 + (0.45 if context.audience else 0) + (0.45 if context.purpose else 0)
            return rating, "The local pass can compare supplied context with the opening, but cannot infer rhetorical success reliably.", "State the exact reader and desired effect, then revise selection, explanation, and tone for that situation.", opening, "The opening provides the strongest available evidence of the implied rhetorical situation.", EvidencePolarity.STRENGTH if context.audience and context.purpose else EvidencePolarity.LIMITATION
        if criterion == "motive":
            rating = 1.7 + min(1.1, signals["motive"] * 0.2) - min(0.45, signals["generic"] * 0.07)
            return rating, "The diagnostic looks for a concrete problem, tension, need, or decision rather than generic importance language.", "Replace broad importance claims with the exact problem, misconception, decision, or unresolved tension.", opening, f"The opening contains {signals['motive']} problem/stakes marker(s) and {signals['generic']} generic significance marker(s).", EvidencePolarity.STRENGTH if signals["motive"] >= 2 else EvidencePolarity.LIMITATION
        if criterion == "controlling_idea":
            opening_words = len(words_in(document.excerpt(opening)))
            rating = 2.0 + (0.45 if 35 <= opening_words <= 180 else 0) + (0.25 if signals["motive"] else 0)
            return rating, "Opening shape offers weak evidence of a governing direction; a substantive reader must judge whether it is meaningful and sustained.", "State the most consequential claim, recommendation, question, or tension precisely enough to guide every major section.", opening, "Readers normally look to the opening for the document's governing direction.", EvidencePolarity.STRENGTH if rating >= 2.5 else EvidencePolarity.LIMITATION
        if criterion == "development":
            rating = 1.55 + min(1.2, stats.paragraph_count * 0.12) + min(0.65, signals["reasoning"] * 0.07)
            return rating, "Visible connective reasoning is only a proxy; it does not prove that warrants are valid.", "After each important example or claim, explain what it shows, how it supports the controlling idea, and why the consequence matters.", representative, f"The document contains {signals['reasoning']} visible reasoning or connective marker(s).", EvidencePolarity.STRENGTH if signals["reasoning"] >= 3 else EvidencePolarity.LIMITATION
        if criterion == "support":
            rating = 1.45 + min(1.85, support_markers * 0.17)
            return rating, "Counts of examples, citations, numbers, and quotations are proxies; relevance and accuracy still require review.", "Ground the most consequential abstract claim in a verifiable source, example, scene, observation, or concrete particular, then interpret it.", representative, f"The document contains {support_markers} visible support marker(s).", EvidencePolarity.STRENGTH if support_markers >= 3 else EvidencePolarity.LIMITATION
        if criterion == "complexity":
            rating = 1.65 + min(1.4, signals["counter"] * 0.14)
            return rating, "Contrast and qualification can indicate complexity, but may also be formulaic or weakly integrated.", "Name the strongest relevant objection, limitation, alternative, or uncertainty and adjust the claim's scope.", representative, f"The document contains {signals['counter']} qualification or counterpressure marker(s).", EvidencePolarity.STRENGTH if signals["counter"] >= 2 else EvidencePolarity.LIMITATION
        if criterion == "macrostructure":
            spread = max(paragraph_lengths) - min(paragraph_lengths) if paragraph_lengths else 0
            rating = 2.0 + (0.45 if 3 <= len(paragraph_lengths) <= 18 else 0) + (0.3 if spread >= 25 else 0)
            return rating, "Paragraph count and proportion are weak evidence of architecture; function and sequence require a reader.", "Reverse-outline every paragraph with a functional verb, then combine repeated functions and move material to reader-need order.", "Document", f"The prose has {len(paragraph_lengths)} paragraph(s) and a paragraph-length spread of {spread} words.", EvidencePolarity.STRENGTH if rating >= 2.5 else EvidencePolarity.LIMITATION
        if criterion == "paragraph_cohesion":
            share = multi_sentence / max(1, len(paragraph_lengths))
            rating = 1.85 + min(0.95, share) - min(0.45, len(stats.repeated_paragraph_openings) * 0.12)
            return rating, "The local pass checks development and repeated openings, not the validity of conceptual transitions.", "Give each paragraph one primary function, develop it fully, and connect its opening to the previous paragraph's established information.", "Document", f"{multi_sentence} paragraph(s) contain multiple sentences; repeated openings: {stats.repeated_paragraph_openings or 'none detected'}.", EvidencePolarity.STRENGTH if share >= 0.6 else EvidencePolarity.LIMITATION
        if criterion == "sentence_craft":
            penalty = (0.35 if stats.longest_sentence_words > 50 else 0) + (0.3 if stats.sentence_count >= 5 and stats.sentence_length_stdev < 4 else 0)
            rating = 2.7 - penalty
            return rating, "Sentence metrics describe possible overload or monotony, but variation is not quality by itself.", "Read the prose aloud and repair sentences whose actors, actions, clause relationships, or emphasis are difficult to recover.", "Document", f"Sentence lengths range from {stats.shortest_sentence_words} to {stats.longest_sentence_words} words; standard deviation is {stats.sentence_length_stdev}.", EvidencePolarity.STRENGTH if rating >= 2.5 else EvidencePolarity.LIMITATION
        if criterion == "diction":
            rating = 2.75 - min(1.0, signals["filler"] * 0.2) - min(0.45, signals["generic"] * 0.05)
            return rating, "The diagnostic flags a narrow set of verbose wrappers and generic significance terms without banning any word.", "Replace abstract or inflated wording with the exact actor, action, distinction, or consequence meant in the passage.", representative, f"The document contains {signals['filler']} verbose wrapper(s) and {signals['generic']} generic significance marker(s).", EvidencePolarity.STRENGTH if signals["filler"] == 0 else EvidencePolarity.LIMITATION
        if criterion == "voice_ethos":
            specificity = support_markers
            rating = 2.05 + min(0.8, specificity * 0.08)
            return rating, "Voice cannot be reduced to first person or stylistic quirks; this pass notices only limited signs of specificity and stance.", "Make an important judgment traceable: state what you notice, why you selected it, and what warrants the choice.", representative, "The longest developed paragraph supplies the densest available sample of stance and particulars.", EvidencePolarity.STRENGTH if specificity >= 3 else EvidencePolarity.LIMITATION
        if criterion == "conventions":
            malformed = sum(1 for sentence in document.sentences() if sentence and sentence[-1] not in ".!?)]\"'”’")
            rating = 3.1 - min(1.2, malformed * 0.18)
            return rating, "This intentionally limited check does not treat one prestige dialect as the sole standard of quality.", "Correct patterns that obstruct meaning, citation, navigation, or accessibility while preserving intentional language variety.", "Document", f"The surface parser found {malformed} sentence(s) without a conventional terminal marker.", EvidencePolarity.STRENGTH if malformed == 0 else EvidencePolarity.LIMITATION
        return 2.0, "This criterion requires substantive human or model judgment.", "Review this dimension with a trained reader.", "Document", "No calibrated local diagnostic exists for this criterion.", EvidencePolarity.LIMITATION

