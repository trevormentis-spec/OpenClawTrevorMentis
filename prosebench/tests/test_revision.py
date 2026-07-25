from prosebench.document import NumberedDocument
from prosebench.models import AssessmentContext
from prosebench.pipeline import AssessmentPipeline, audit_locked_tokens
from prosebench.providers import LocalDiagnosticProvider
from prosebench.rubric import RubricLoader


def test_local_revision_preserves_number_and_removes_wrapper() -> None:
    document = NumberedDocument.from_text(
        "memo.md",
        "In order to reduce the delay, the team reviewed 42 cases. "
        "It is important to note that the result was limited.",
    )
    rubric = RubricLoader().load("professional_prose")
    pipeline = AssessmentPipeline(LocalDiagnosticProvider())
    assessment = pipeline.assess(document, rubric, AssessmentContext())
    revision = pipeline.revise(
        document,
        rubric,
        assessment,
        ["diction"],
        "suggestions",
        "strict",
    )
    assert "To reduce" in revision.rewritten_text
    assert "42" in revision.rewritten_text
    assert not [
        item
        for item in revision.claim_audit
        if item.value == "42" and item.status != "preserved"
    ]


def test_claim_audit_flags_added_number() -> None:
    audit = audit_locked_tokens(
        "The result improved.",
        "The result improved by 25%.",
    )
    assert any(item.value == "25%" and item.status == "added" for item in audit)
