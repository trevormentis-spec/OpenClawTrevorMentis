from pathlib import Path

from prosebench.document import NumberedDocument
from prosebench.models import AssessmentContext
from prosebench.pipeline import AssessmentPipeline
from prosebench.providers import LocalDiagnosticProvider
from prosebench.reports import ReportWriter
from prosebench.rubric import RubricLoader


def test_assessment_bundle_writes_all_formats(tmp_path: Path) -> None:
    document = NumberedDocument.from_text(
        "essay.md",
        "A problem needs a decision.\n\nFor example, one option costs 42 dollars.",
    )
    assessment = AssessmentPipeline(LocalDiagnosticProvider()).assess(
        document,
        RubricLoader().load("academic_argument"),
        AssessmentContext(),
    )
    paths = ReportWriter().write_assessment_bundle(assessment, tmp_path, "essay")
    assert set(paths) == {"markdown", "html", "json"}
    assert all(path.exists() for path in paths.values())
    assert "ProseBench assessment" in paths["markdown"].read_text(encoding="utf-8")
