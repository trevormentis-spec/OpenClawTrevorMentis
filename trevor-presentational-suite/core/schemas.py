"""TPS Schemas — all pydantic v2 models for the presentational suite.

Central schema file. Every other TPS module imports from here.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class AssetKind(str, Enum):
    MAP = "map"
    DIAGRAM = "diagram"
    CHART = "chart"
    INFOGRAPHIC = "infographic"
    ILLUSTRATION = "illustration"
    TABLE = "table"
    NARRATION = "narration"
    VIDEO = "video"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    AUTO_APPROVED = "auto_approved"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeliverableKind(str, Enum):
    PDF = "pdf"
    WEBSITE = "website"
    SOCIAL_PACK = "social_pack"
    BRIEFING_VIDEO = "briefing_video"
    DECK = "deck"
    EXEC_CARD = "exec_card"


class QCStatus(str, Enum):
    PENDING_REVIEW = "pending_human_analyst_qc_review"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── Ingest Models ────────────────────────────────────────────────────────────


class IngestSource(BaseModel):
    """A source reference from a TREVOR brief."""
    id: str = ""
    name: str
    admiralty: str = ""
    source_type: str = ""
    language: str = ""
    url: str = ""
    themes: list[str] = Field(default_factory=list)


class IngestJudgment(BaseModel):
    """A calibrated judgment from a TREVOR brief."""
    id: str = ""
    claim: str
    kent_band: str = ""
    pct_range: list[int] = Field(default_factory=lambda: [0, 0])
    horizon_end: str = ""
    sources: list[IngestSource] = Field(default_factory=list)
    subscriber_action: str = ""


class IngestSubsection(BaseModel):
    """A subsection within a TREVOR brief section."""
    id: str = ""
    title: str
    narrative: str = ""
    judgments: list[IngestJudgment] = Field(default_factory=list)
    subscriber_action: str = ""
    themes: list[str] = Field(default_factory=list)


class IngestSection(BaseModel):
    """A top-level section of a TREVOR brief."""
    id: str = ""
    title: str
    narrative: str = ""
    subsections: list[IngestSubsection] = Field(default_factory=list)
    judgments: list[IngestJudgment] = Field(default_factory=list)
    geographic: Optional[dict] = None
    themes: list[str] = Field(default_factory=list)


class IngestWatchItem(BaseModel):
    """An Indicators & Warnings watch item."""
    id: str = ""
    indicator: str
    trigger: str = ""
    signal: str = ""
    upgrade_signal: str = ""
    downgrade_signal: str = ""


class IngestTradePosition(BaseModel):
    """A trade/hedge position recommendation."""
    id: str = ""
    instrument: str
    instrument_type: str = ""
    strike: str = ""
    price: Optional[float] = None
    price_as_of: str = ""
    recommendation: str = ""
    sizing_usd: Optional[float] = None
    sizing_methodology: str = ""
    rationale: str = ""
    is_proxy: bool = False


class IngestGap(BaseModel):
    """A framework gap / intelligence limitation."""
    id: str = ""
    description: str
    impact: str = ""
    next_step: str = ""
    estimated_cost: str = ""
    timeline: str = ""


class IngestActionLine(BaseModel):
    """A prioritized action for the subscriber."""
    id: str = ""
    priority: int = 3
    action: str
    timeframe: str = ""
    rationale: str = ""


class IngestedBrief(BaseModel):
    """Typed representation of a TREVOR brief, parsed from JSON.

    This is the bridge between TREVOR's native output and TPS.
    All downstream TPS processing works with this model.
    """
    brief_id: str = ""
    schema_version: str = ""
    title: str = ""
    query_type: str = ""
    produced_at: str = ""
    producer: str = ""
    bluf: str = ""
    calibration_band: str = ""
    calibration_pct_range: list[int] = Field(default_factory=lambda: [0, 0])
    headline_judgments: list[IngestJudgment] = Field(default_factory=list)
    sections: list[IngestSection] = Field(default_factory=list)
    watch_items: list[IngestWatchItem] = Field(default_factory=list)
    trade_positions: list[IngestTradePosition] = Field(default_factory=list)
    gaps: list[IngestGap] = Field(default_factory=list)
    action_lines: list[IngestActionLine] = Field(default_factory=list)
    sources: list[IngestSource] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    generation_metadata: dict = Field(default_factory=dict)
    raw: dict = Field(default_factory=dict)


# ── Plan Models ──────────────────────────────────────────────────────────────


class AssetSpec(BaseModel):
    """Specification for a single visual asset to generate."""
    asset_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    kind: AssetKind
    generator: str  # e.g. "mermaid", "mapbox_static", "flux2pro"
    title: str
    prompt: str = ""
    source_section_idx: Optional[int] = None
    estimated_cost_usd: float = 0.0
    estimated_time_sec: float = 0.0
    depends_on: list[str] = Field(default_factory=list)
    parameters: dict = Field(default_factory=dict)


class PresentationPlan(BaseModel):
    """Complete plan for visualizing a TREVOR brief."""
    plan_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    brief_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assets: list[AssetSpec] = Field(default_factory=list)
    deliverables: list[DeliverableKind] = Field(default_factory=list)
    style_brief: str = ""
    total_estimated_cost_usd: float = 0.0
    total_estimated_time_sec: float = 0.0
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: str = ""
    approved_at: Optional[datetime] = None


# ── Provenance Models ────────────────────────────────────────────────────────


class AssetProvenance(BaseModel):
    """Provenance record for a generated asset."""
    asset_id: str
    plan_id: str
    brief_id: str
    kind: AssetKind
    generator: str
    model_used: str = ""
    provider: str = ""
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    generation_time_sec: float = 0.0
    input_hash: str = ""
    output_path: str = ""
    output_hash: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    qc_status: QCStatus = QCStatus.PENDING_REVIEW
    qc_reviewer: str = ""
    qc_timestamp: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


# ── Cost Estimation Models ───────────────────────────────────────────────────


class CostEstimate(BaseModel):
    """Cost estimate for a single asset."""
    asset_id: str = ""
    kind: AssetKind = AssetKind.DIAGRAM
    generator: str = ""
    estimated_cost_usd: float = 0.0
    estimated_time_sec: float = 0.0
    breakdown: dict = Field(default_factory=dict)
    requires_approval: bool = False


class PlanCostEstimate(BaseModel):
    """Aggregate cost estimate for a full presentation plan."""
    plan_id: str
    assets: list[CostEstimate] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_time_sec: float = 0.0
    expensive_assets: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    stale_pricing_warnings: list[str] = Field(default_factory=list)
