from __future__ import annotations

import html
from pathlib import Path

from prosebench.models import AssessmentResult, CoachingPlan, ComparisonResult, RevisionResult


class ReportWriter:
    """Write stable, human-readable and machine-readable report bundles."""

    def write_assessment_bundle(
        self,
        result: AssessmentResult,
        output_dir: Path,
        stem: str,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "markdown": output_dir / f"{stem}-assessment.md",
            "html": output_dir / f"{stem}-assessment.html",
            "json": output_dir / f"{stem}-assessment.json",
        }
        paths["markdown"].write_text(render_assessment_markdown(result), encoding="utf-8")
        paths["html"].write_text(render_assessment_html(result), encoding="utf-8")
        paths["json"].write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return paths

    def write_coaching_plan(
        self,
        plan: CoachingPlan,
        output_dir: Path,
        stem: str,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "markdown": output_dir / f"{stem}-coach.md",
            "json": output_dir / f"{stem}-coach.json",
        }
        paths["markdown"].write_text(render_coaching_markdown(plan), encoding="utf-8")
        paths["json"].write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return paths

    def write_revision_bundle(
        self,
        result: RevisionResult,
        output_dir: Path,
        stem: str,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "revised": output_dir / f"{stem}-revised.md",
            "diff": output_dir / f"{stem}-revision.diff",
            "report": output_dir / f"{stem}-revision.md",
            "json": output_dir / f"{stem}-revision.json",
        }
        paths["revised"].write_text(result.rewritten_text.rstrip() + "\n", encoding="utf-8")
        paths["diff"].write_text(result.unified_diff.rstrip() + "\n", encoding="utf-8")
        paths["report"].write_text(render_revision_markdown(result), encoding="utf-8")
        paths["json"].write_text(
            result.model_dump_json(indent=2, exclude={"original_text", "rewritten_text"}),
            encoding="utf-8",
        )
        return paths

    def write_comparison(
        self,
        result: ComparisonResult,
        output_dir: Path,
        stem: str,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "markdown": output_dir / f"{stem}-comparison.md",
            "diff": output_dir / f"{stem}-comparison.diff",
            "json": output_dir / f"{stem}-comparison.json",
        }
        paths["markdown"].write_text(render_comparison_markdown(result), encoding="utf-8")
        paths["diff"].write_text(result.unified_diff.rstrip() + "\n", encoding="utf-8")
        paths["json"].write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return paths


def render_assessment_markdown(result: AssessmentResult) -> str:
    lines = [
        "# ProseBench assessment",
        "",
        f"- **Document:** `{result.document_name}`",
        f"- **Profile:** `{result.profile}` v{result.profile_version}",
        f"- **Provider:** `{result.provider}` / `{result.model}`",
        f"- **Overall quality:** **{result.overall_score:.2f} / 100**",
        f"- **Assessment confidence:** **{result.overall_confidence.value}**",
        f"- **Integrity status:** **{result.integrity_status.value}**",
        "",
        "## Reader's account",
        "",
        result.reader_account,
        "",
        "## Priority revisions",
        "",
    ]
    if result.priorities:
        lines.extend(f"{index}. {priority}" for index, priority in enumerate(result.priorities, 1))
    else:
        lines.append("No priorities were returned.")

    lines.extend(["", "## Strengths", ""])
    if result.strengths:
        lines.extend(f"- {strength}" for strength in result.strengths)
    else:
        lines.append("- No strengths were returned.")

    lines.extend(
        [
            "",
            "## Scorecard",
            "",
            "| Criterion | Rating | Points | Confidence |",
            "|---|---:|---:|---|",
        ]
    )
    for item in result.criteria:
        lines.append(
            f"| {item.label} | {item.rating:.2f}/4 | "
            f"{item.points:.2f}/{item.weight:g} | {item.confidence.value} |"
        )

    for item in result.criteria:
        lines.extend(
            [
                "",
                f"## {item.label}",
                "",
                f"**Rating:** {item.rating:.2f}/4  ",
                f"**Points:** {item.points:.2f}/{item.weight:g}  ",
                f"**Confidence:** {item.confidence.value}",
                "",
                item.rationale,
                "",
                "### Evidence",
                "",
            ]
        )
        for evidence in item.evidence:
            excerpt = f' — “{evidence.excerpt}”' if evidence.excerpt else ""
            lines.append(
                f"- **{evidence.polarity.value.title()} · {evidence.location}:** "
                f"{evidence.interpretation}{excerpt}"
            )
        lines.extend(["", f"**Revision action:** {item.revision_action}"])

    lines.extend(["", "## Integrity notes", ""])
    if result.integrity_notes:
        lines.extend(f"- {note}" for note in result.integrity_notes)
    else:
        lines.append("- No integrity notes supplied.")

    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)

    lines.extend(
        [
            "",
            "---",
            "",
            "This report is a structured second-reader judgment, not proof of authorship, "
            "originality, factual accuracy, or policy compliance.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_assessment_html(result: AssessmentResult) -> str:
    score_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.label)}</td>"
        f"<td>{item.rating:.2f}/4</td>"
        f"<td>{item.points:.2f}/{item.weight:g}</td>"
        f"<td>{html.escape(item.confidence.value)}</td>"
        "</tr>"
        for item in result.criteria
    )
    sections: list[str] = []
    for item in result.criteria:
        evidence_items: list[str] = []
        for evidence in item.evidence:
            excerpt = (
                f"<blockquote>{html.escape(evidence.excerpt)}</blockquote>"
                if evidence.excerpt
                else ""
            )
            evidence_items.append(
                "<li>"
                f"<strong>{html.escape(evidence.polarity.value.title())} · "
                f"{html.escape(evidence.location)}</strong>: "
                f"{html.escape(evidence.interpretation)}{excerpt}"
                "</li>"
            )
        sections.append(
            "<section>"
            f"<h2>{html.escape(item.label)}</h2>"
            f"<p><strong>{item.rating:.2f}/4 · {item.points:.2f}/{item.weight:g} points · "
            f"{html.escape(item.confidence.value)} confidence</strong></p>"
            f"<p>{html.escape(item.rationale)}</p>"
            f"<h3>Evidence</h3><ul>{''.join(evidence_items)}</ul>"
            f"<p><strong>Revision action:</strong> {html.escape(item.revision_action)}</p>"
            "</section>"
        )

    priorities = "".join(f"<li>{html.escape(value)}</li>" for value in result.priorities)
    strengths = "".join(f"<li>{html.escape(value)}</li>" for value in result.strengths)
    warnings = "".join(f"<li>{html.escape(value)}</li>" for value in result.warnings)
    warning_block = (
        f'<aside class="warning"><h2>Warnings</h2><ul>{warnings}</ul></aside>'
        if warnings
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ProseBench assessment: {html.escape(result.document_name)}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 980px; margin: 0 auto; padding: 40px 24px; line-height: 1.6; color: #191919; }}
    header {{ border-bottom: 3px solid #191919; margin-bottom: 32px; }}
    .score {{ font-size: 2rem; font-weight: 750; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th, td {{ border: 1px solid #d5d5d5; padding: 9px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f3f3; }}
    section {{ border-top: 1px solid #ddd; padding-top: 18px; margin-top: 30px; }}
    blockquote {{ border-left: 4px solid #bbb; margin: 10px 0; padding: 6px 14px; background: #fafafa; }}
    .warning {{ background: #fff4d8; border: 1px solid #e7c66d; padding: 14px; margin-top: 28px; }}
    footer {{ margin-top: 40px; font-size: .92rem; color: #555; }}
  </style>
</head>
<body>
  <header>
    <h1>ProseBench assessment</h1>
    <p>{html.escape(result.document_name)} · {html.escape(result.profile)} v{html.escape(result.profile_version)}</p>
    <p class="score">{result.overall_score:.2f} / 100</p>
    <p>{html.escape(result.overall_confidence.value)} confidence · integrity: {html.escape(result.integrity_status.value)}</p>
  </header>
  <h2>Reader's account</h2>
  <p>{html.escape(result.reader_account)}</p>
  <h2>Priority revisions</h2><ol>{priorities}</ol>
  <h2>Strengths</h2><ul>{strengths}</ul>
  <h2>Scorecard</h2>
  <table><thead><tr><th>Criterion</th><th>Rating</th><th>Points</th><th>Confidence</th></tr></thead><tbody>{score_rows}</tbody></table>
  {''.join(sections)}
  {warning_block}
  <footer><p>This report is a structured second-reader judgment, not proof of authorship, originality, factual accuracy, or policy compliance.</p></footer>
</body>
</html>
"""


def render_coaching_markdown(plan: CoachingPlan) -> str:
    lines = [
        "# ProseBench revision plan",
        "",
        f"**Document:** `{plan.document_name}`  ",
        f"**Profile:** `{plan.profile}`",
        "",
        "## Reader experience",
        "",
        plan.reader_experience,
        "",
        "## Revision order",
        "",
    ]
    for priority in plan.priorities:
        lines.extend(
            [
                f"### {priority.order}. {priority.title}",
                "",
                priority.why,
                "",
                f"**Locations:** {', '.join(priority.locations) if priority.locations else 'Document-wide'}",
                "",
                "**Actions:**",
            ]
        )
        lines.extend(f"- {action}" for action in priority.actions)
        lines.append("")

    lines.extend(["## Defer until later", ""])
    lines.extend(f"- {item}" for item in plan.defer_until_later)
    if plan.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in plan.warnings)
    return "\n".join(lines) + "\n"


def render_revision_markdown(result: RevisionResult) -> str:
    lines = [
        "# ProseBench revision report",
        "",
        f"- **Document:** `{result.document_name}`",
        f"- **Provider:** `{result.provider}` / `{result.model}`",
        f"- **Profile:** `{result.profile}`",
        f"- **Mode:** `{result.mode}`",
        f"- **Fact lock:** `{result.fact_lock}`",
        f"- **Focus:** {', '.join(result.focus) if result.focus else 'Highest-impact assessed weaknesses'}",
        "",
        "## Change log",
        "",
    ]
    if result.change_log:
        for item in result.change_log:
            lines.extend(
                [
                    f"### {item.location}",
                    "",
                    f"- **Criteria:** {', '.join(item.criterion_ids) or 'General'}",
                    f"- **Reason:** {item.reason}",
                    f"- **Before:** {item.before or '(structural change)'}",
                    f"- **After:** {item.after or '(structural change)'}",
                    "",
                ]
            )
    else:
        lines.append("No explicit change log was returned.")

    lines.extend(
        [
            "",
            "## Claim-lock audit",
            "",
            "| Type | Value | Status | Note |",
            "|---|---|---|---|",
        ]
    )
    if result.claim_audit:
        for item in result.claim_audit:
            value = item.value.replace("|", "\\|").replace("`", "\\`")
            note = item.note.replace("|", "\\|")
            lines.append(f"| {item.token_type} | `{value}` | {item.status} | {note} |")
    else:
        lines.append("| — | No locked tokens detected | — | — |")

    if result.unresolved_issues:
        lines.extend(["", "## Unresolved issues", ""])
        lines.extend(f"- {item}" for item in result.unresolved_issues)
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in result.warnings)
    return "\n".join(lines) + "\n"


def render_comparison_markdown(result: ComparisonResult) -> str:
    average_delta = result.after_metrics.average_sentence_words - result.before_metrics.average_sentence_words
    stdev_delta = result.after_metrics.sentence_length_stdev - result.before_metrics.sentence_length_stdev
    lines = [
        "# ProseBench draft comparison",
        "",
        f"**Before:** `{result.before_name}`  ",
        f"**After:** `{result.after_name}`",
        "",
        "## Document metrics",
        "",
        "| Metric | Before | After | Delta |",
        "|---|---:|---:|---:|",
        f"| Words | {result.before_metrics.word_count} | {result.after_metrics.word_count} | {result.word_count_delta:+d} |",
        f"| Sentences | {result.before_metrics.sentence_count} | {result.after_metrics.sentence_count} | {result.sentence_count_delta:+d} |",
        f"| Paragraphs | {result.before_metrics.paragraph_count} | {result.after_metrics.paragraph_count} | {result.paragraph_count_delta:+d} |",
        f"| Average sentence words | {result.before_metrics.average_sentence_words:.2f} | {result.after_metrics.average_sentence_words:.2f} | {average_delta:+.2f} |",
        f"| Sentence-length stdev | {result.before_metrics.sentence_length_stdev:.2f} | {result.after_metrics.sentence_length_stdev:.2f} | {stdev_delta:+.2f} |",
    ]
    if result.score_before is not None and result.score_after is not None:
        score_delta = result.score_delta or 0.0
        lines.extend(
            [
                "",
                "## Assessment delta",
                "",
                f"**Overall:** {result.score_before:.2f} → {result.score_after:.2f} ({score_delta:+.2f})",
                "",
                "| Criterion | Before | After | Points delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for item in result.criterion_deltas:
            lines.append(
                f"| {item.label} | {item.before_rating:.2f} | {item.after_rating:.2f} | {item.points_delta:+.2f} |"
            )

    lines.extend(["", "## Unified diff", "", "```diff", result.unified_diff, "```"])
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    return "\n".join(lines) + "\n"
