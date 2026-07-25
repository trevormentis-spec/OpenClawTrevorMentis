from prosebench.document import NumberedDocument
from prosebench.models import AssessmentContext
from prosebench.pipeline import AssessmentPipeline
from prosebench.providers import LocalDiagnosticProvider
from prosebench.rubric import RubricLoader


def test_local_assessment_is_complete_and_low_confidence() -> None:
    document = NumberedDocument.from_text(
        "essay.md",
        "A policy dispute creates a practical problem. The city must decide which systems need review.\n\n"
        "For example, a benefits model can affect eligibility. However, a scheduling tool usually cannot.\n\n"
        "The policy should distinguish those uses because their consequences differ.",
    )
    rubric = RubricLoader().load("academic_argument")
    result = AssessmentPipeline(LocalDiagnosticProvider()).assess(
        document,
        rubric,
        AssessmentContext(
            audience="city council",
            purpose="recommend a policy distinction",
        ),
    )
    assert len(result.criteria) == 12
    assert 0 <= result.overall_score <= 100
    assert result.overall_confidence.value == "low"
    assert all(item.evidence for item in result.criteria)
    assert {item.criterion_id for item in result.criteria} == {
        item.criterion_id for item in rubric.criteria
    }


def test_coaching_plan_prioritizes_three_dimensions() -> None:
    document = NumberedDocument.from_text(
        "short.md",
        "This topic is important. It is very significant.",
    )
    rubric = RubricLoader().load("academic_argument")
    pipeline = AssessmentPipeline(LocalDiagnosticProvider())
    assessment = pipeline.assess(document, rubric, AssessmentContext())
    plan = pipeline.coach(assessment)
    assert len(plan.priorities) == 3
    assert [item.order for item in plan.priorities] == [1, 2, 3]
    assert plan.defer_until_later
