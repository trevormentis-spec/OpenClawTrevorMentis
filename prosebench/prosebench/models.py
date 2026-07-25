from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IntegrityStatus(str, Enum):
    CLEAR = "clear"
    REVIEW_NEEDED = "review_needed"
    MATERIAL_FAILURE = "material_failure"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"


class EvidencePolarity(str, Enum):
    STRENGTH = "strength"
    LIMITATION = "limitation"


class EvidenceItem(BaseModel):
    location: str = Field(description="Paragraph location such as P3, or Document")
    excerpt: str = Field(default="", max_length=1200)
    interpretation: str
    polarity: EvidencePolarity


class CriterionDraft(BaseModel):
    criterion_id: str
    rating: float = Field(ge=0, le=4)
    confidence: Confidence
    rationale: str
    evidence: list[EvidenceItem] = Field(min_length=1)
    revision_action: str


class ProviderAssessmentDraft(BaseModel):
    reader_account: str
    strengths: list[str] = Field(default_factory=list, max_length=5)
    priorities: list[str] = Field(default_factory=list, max_length=5)
    criteria: list[CriterionDraft] = Field(min_length=1)
    integrity_status: IntegrityStatus = IntegrityStatus.NOT_CHECKED
    integrity_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AssessmentContext(BaseModel):
    audience: str = ""
    purpose: str = ""
    genre: str = ""
    brief: str = ""
    ai_use_level: str = ""


class DocumentStats(BaseModel):
    word_count: int
    sentence_count: int
    paragraph_count: int
    average_sentence_words: float
    sentence_length_stdev: float
    shortest_sentence_words: int
    longest_sentence_words: int
    citation_count: int
    quotation_count: int
    number_count: int
    first_person_count: int
    repeated_paragraph_openings: list[str] = Field(default_factory=list)


class CriterionAssessment(BaseModel):
    criterion_id: str
    label: str
    question: str
    rating: float = Field(ge=0, le=4)
    weight: float = Field(gt=0)
    points: float = Field(ge=0)
    confidence: Confidence
    rationale: str
    evidence: list[EvidenceItem]
    revision_action: str


class AssessmentResult(BaseModel):
    schema_version: str = "1.0"
    document_name: str
    profile: str
    profile_version: str
    provider: str
    model: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context: AssessmentContext
    document_stats: DocumentStats
    reader_account: str
    strengths: list[str]
    priorities: list[str]
    criteria: list[CriterionAssessment]
    overall_score: float = Field(ge=0, le=100)
    overall_confidence: Confidence
    integrity_status: IntegrityStatus
    integrity_notes: list[str]
    warnings: list[str]


class RevisionPriority(BaseModel):
    order: int = Field(ge=1)
    criterion_id: str
    title: str
    why: str
    locations: list[str] = Field(default_factory=list)
    actions: list[str] = Field(min_length=1)


class CoachingPlan(BaseModel):
    schema_version: str = "1.0"
    document_name: str
    profile: str
    reader_experience: str
    priorities: list[RevisionPriority]
    defer_until_later: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ChangeLogItem(BaseModel):
    location: str = "Document"
    criterion_ids: list[str] = Field(default_factory=list)
    before: str = ""
    after: str = ""
    reason: str


class ClaimAuditItem(BaseModel):
    token_type: Literal["number", "url", "citation", "quotation", "name", "other"]
    value: str
    status: Literal["preserved", "added", "removed", "changed", "review"]
    note: str = ""


class ProviderRevisionDraft(BaseModel):
    rewritten_text: str
    change_log: list[ChangeLogItem] = Field(default_factory=list)
    claim_audit: list[ClaimAuditItem] = Field(default_factory=list)
    unresolved_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RevisionResult(BaseModel):
    schema_version: str = "1.0"
    document_name: str
    provider: str
    model: str
    profile: str
    focus: list[str]
    mode: str
    fact_lock: str
    original_text: str
    rewritten_text: str
    unified_diff: str
    change_log: list[ChangeLogItem]
    claim_audit: list[ClaimAuditItem]
    unresolved_issues: list[str]
    warnings: list[str]


class MetricSnapshot(BaseModel):
    word_count: int
    sentence_count: int
    paragraph_count: int
    average_sentence_words: float
    sentence_length_stdev: float


class CriterionDelta(BaseModel):
    criterion_id: str
    label: str
    before_rating: float
    after_rating: float
    rating_delta: float
    before_points: float
    after_points: float
    points_delta: float


class ComparisonResult(BaseModel):
    schema_version: str = "1.0"
    before_name: str
    after_name: str
    before_metrics: MetricSnapshot
    after_metrics: MetricSnapshot
    word_count_delta: int
    sentence_count_delta: int
    paragraph_count_delta: int
    unified_diff: str
    score_before: float | None = None
    score_after: float | None = None
    score_delta: float | None = None
    criterion_deltas: list[CriterionDelta] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
