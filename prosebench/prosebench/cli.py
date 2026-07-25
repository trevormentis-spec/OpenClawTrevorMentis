from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from prosebench import __version__
from prosebench.document import NumberedDocument
from prosebench.models import AssessmentContext, AssessmentResult
from prosebench.pipeline import AssessmentPipeline, compare_documents
from prosebench.providers import LocalDiagnosticProvider, OpenAIProvider, ProseProvider
from prosebench.reports import ReportWriter
from prosebench.rubric import RubricLoader, RubricProfile

load_dotenv()

app = typer.Typer(
    name="prosebench",
    help="Transparent, rubric-driven prose assessment and controlled revision.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"ProseBench {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Assess, coach, revise, and compare prose without inferring authorship."""


@app.command()
def profiles() -> None:
    """List bundled rubric profiles."""
    loader = RubricLoader()
    table = Table(title="ProseBench rubric profiles")
    table.add_column("Profile")
    table.add_column("Label")
    table.add_column("Description")
    for name in loader.available_profiles():
        profile = loader.load(name)
        table.add_row(name, profile.label, profile.description)
    console.print(table)


@app.command()
def assess(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    profile: Annotated[str, typer.Option("--profile", "-p")] = "academic_argument",
    provider: Annotated[str, typer.Option("--provider", help="auto, openai, or local")] = "auto",
    model: Annotated[str | None, typer.Option("--model", help="OpenAI model override")] = None,
    audience: Annotated[str, typer.Option("--audience")] = "",
    purpose: Annotated[str, typer.Option("--purpose")] = "",
    genre: Annotated[str, typer.Option("--genre")] = "",
    brief: Annotated[Path | None, typer.Option("--brief", exists=True, dir_okay=False)] = None,
    ai_use_level: Annotated[str, typer.Option("--ai-use-level")] = "",
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("prosebench-reports"),
) -> None:
    """Assess a document and write Markdown, HTML, and JSON reports."""
    try:
        document, rubric, context, pipeline = _setup(
            file=file,
            profile=profile,
            provider_name=provider,
            model=model,
            audience=audience,
            purpose=purpose,
            genre=genre,
            brief=brief,
            ai_use_level=ai_use_level,
        )
        result = pipeline.assess(document, rubric, context)
        paths = ReportWriter().write_assessment_bundle(result, output_dir, file.stem)
        _print_assessment(result)
        _print_paths(paths)
    except Exception as exc:
        _fail(exc)


@app.command()
def coach(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    profile: Annotated[str, typer.Option("--profile", "-p")] = "academic_argument",
    provider: Annotated[str, typer.Option("--provider")] = "auto",
    model: Annotated[str | None, typer.Option("--model")] = None,
    audience: Annotated[str, typer.Option("--audience")] = "",
    purpose: Annotated[str, typer.Option("--purpose")] = "",
    genre: Annotated[str, typer.Option("--genre")] = "",
    brief: Annotated[Path | None, typer.Option("--brief", exists=True, dir_okay=False)] = None,
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("prosebench-reports"),
) -> None:
    """Create a prioritized global revision plan without altering the source."""
    try:
        document, rubric, context, pipeline = _setup(
            file=file,
            profile=profile,
            provider_name=provider,
            model=model,
            audience=audience,
            purpose=purpose,
            genre=genre,
            brief=brief,
            ai_use_level="",
        )
        result = pipeline.assess(document, rubric, context)
        plan = pipeline.coach(result)
        writer = ReportWriter()
        assessment_paths = writer.write_assessment_bundle(result, output_dir, file.stem)
        plan_paths = writer.write_coaching_plan(plan, output_dir, file.stem)
        console.print(f"[bold]Revision plan for {file.name}[/bold]")
        for priority in plan.priorities:
            console.print(
                f"{priority.order}. [bold]{priority.title}[/bold] — {priority.actions[0]}"
            )
        all_paths = dict(assessment_paths)
        all_paths.update({f"coach_{key}": value for key, value in plan_paths.items()})
        _print_paths(all_paths)
    except Exception as exc:
        _fail(exc)


@app.command()
def revise(
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    profile: Annotated[str, typer.Option("--profile", "-p")] = "academic_argument",
    provider: Annotated[str, typer.Option("--provider")] = "auto",
    model: Annotated[str | None, typer.Option("--model")] = None,
    focus: Annotated[
        str,
        typer.Option("--focus", help="Comma-separated criterion IDs or labels"),
    ] = "",
    mode: Annotated[str, typer.Option("--mode", help="suggestions or full")] = "suggestions",
    fact_lock: Annotated[str, typer.Option("--fact-lock", help="strict or review")] = "strict",
    audience: Annotated[str, typer.Option("--audience")] = "",
    purpose: Annotated[str, typer.Option("--purpose")] = "",
    genre: Annotated[str, typer.Option("--genre")] = "",
    brief: Annotated[Path | None, typer.Option("--brief", exists=True, dir_okay=False)] = None,
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("prosebench-reports"),
) -> None:
    """Create a separate fact-locked candidate revision and unified diff."""
    try:
        if mode not in {"suggestions", "full"}:
            raise ValueError("--mode must be suggestions or full.")
        if fact_lock not in {"strict", "review"}:
            raise ValueError("--fact-lock must be strict or review.")
        document, rubric, context, pipeline = _setup(
            file=file,
            profile=profile,
            provider_name=provider,
            model=model,
            audience=audience,
            purpose=purpose,
            genre=genre,
            brief=brief,
            ai_use_level="",
        )
        assessment = pipeline.assess(document, rubric, context)
        focus_values = [item.strip() for item in focus.split(",") if item.strip()]
        result = pipeline.revise(
            document,
            rubric,
            assessment,
            focus_values,
            mode,
            fact_lock,
        )
        writer = ReportWriter()
        assessment_paths = writer.write_assessment_bundle(assessment, output_dir, file.stem)
        revision_paths = writer.write_revision_bundle(result, output_dir, file.stem)
        risky = sum(item.status != "preserved" for item in result.claim_audit)
        console.print(f"[bold]Candidate revision created for {file.name}[/bold]")
        console.print(f"Claim-lock items requiring attention: [bold]{risky}[/bold]")
        all_paths = {f"assessment_{key}": value for key, value in assessment_paths.items()}
        all_paths.update({f"revision_{key}": value for key, value in revision_paths.items()})
        _print_paths(all_paths)
    except Exception as exc:
        _fail(exc)


@app.command()
def compare(
    before: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    after: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    assess_both: Annotated[
        bool,
        typer.Option("--assess", help="Run the rubric assessor on both drafts"),
    ] = False,
    profile: Annotated[str, typer.Option("--profile", "-p")] = "academic_argument",
    provider: Annotated[str, typer.Option("--provider")] = "auto",
    model: Annotated[str | None, typer.Option("--model")] = None,
    audience: Annotated[str, typer.Option("--audience")] = "",
    purpose: Annotated[str, typer.Option("--purpose")] = "",
    genre: Annotated[str, typer.Option("--genre")] = "",
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("prosebench-reports"),
) -> None:
    """Compare two drafts with metrics, diff, and optional assessment deltas."""
    try:
        before_doc = NumberedDocument.from_path(before)
        after_doc = NumberedDocument.from_path(after)
        before_assessment = after_assessment = None
        if assess_both:
            rubric = RubricLoader().load(profile)
            selected_provider = _make_provider(provider, model)
            pipeline = AssessmentPipeline(selected_provider)
            context = AssessmentContext(audience=audience, purpose=purpose, genre=genre)
            before_assessment = pipeline.assess(before_doc, rubric, context)
            after_assessment = pipeline.assess(after_doc, rubric, context)
        result = compare_documents(
            before_doc,
            after_doc,
            before_assessment,
            after_assessment,
        )
        paths = ReportWriter().write_comparison(
            result,
            output_dir,
            f"{before.stem}-to-{after.stem}",
        )
        console.print(
            f"Words: {result.before_metrics.word_count} → {result.after_metrics.word_count} "
            f"({result.word_count_delta:+d})"
        )
        if result.score_delta is not None:
            console.print(
                f"Score: {result.score_before:.2f} → {result.score_after:.2f} "
                f"({result.score_delta:+.2f})"
            )
        _print_paths(paths)
    except Exception as exc:
        _fail(exc)


def _setup(
    *,
    file: Path,
    profile: str,
    provider_name: str,
    model: str | None,
    audience: str,
    purpose: str,
    genre: str,
    brief: Path | None,
    ai_use_level: str,
) -> tuple[NumberedDocument, RubricProfile, AssessmentContext, AssessmentPipeline]:
    document = NumberedDocument.from_path(file)
    rubric = RubricLoader().load(profile)
    selected_provider = _make_provider(provider_name, model)
    brief_text = brief.read_text(encoding="utf-8") if brief else ""
    context = AssessmentContext(
        audience=audience,
        purpose=purpose,
        genre=genre,
        brief=brief_text,
        ai_use_level=ai_use_level,
    )
    return document, rubric, context, AssessmentPipeline(selected_provider)


def _make_provider(provider_name: str, model: str | None) -> ProseProvider:
    normalized = provider_name.lower().strip()
    if normalized == "auto":
        normalized = "openai" if os.getenv("OPENAI_API_KEY") else "local"
    if normalized == "openai":
        return OpenAIProvider(model=model)
    if normalized == "local":
        return LocalDiagnosticProvider()
    raise ValueError("--provider must be auto, openai, or local.")


def _print_assessment(result: AssessmentResult) -> None:
    table = Table(title=f"ProseBench assessment: {result.document_name}")
    table.add_column("Criterion")
    table.add_column("Rating", justify="right")
    table.add_column("Points", justify="right")
    table.add_column("Confidence")
    for item in result.criteria:
        table.add_row(
            item.label,
            f"{item.rating:.2f}/4",
            f"{item.points:.2f}/{item.weight:g}",
            item.confidence.value,
        )
    console.print(table)
    console.print(
        f"Overall: [bold]{result.overall_score:.2f}/100[/bold] · "
        f"confidence: {result.overall_confidence.value}"
    )


def _print_paths(paths: dict[str, Path]) -> None:
    console.print("\n[bold]Written files[/bold]")
    for label, path in paths.items():
        console.print(f"- {label}: {path.resolve()}")


def _fail(exc: Exception) -> None:
    console.print(f"[bold red]Error:[/bold red] {exc}")
    raise typer.Exit(code=1)
