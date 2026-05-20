"""TPS ORM Models — SQLAlchemy 2.x declarative models.

Tables:
- tps_plans: presentation plans with approval state
- tps_assets: generated assets with status and output paths
- tps_provenance: append-only generation event ledger
- tps_source_events: structured intelligence events for charting
- tps_indicator_history: I&W indicator time series
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class PlanRecord(Base):
    """A presentation plan submitted for approval and execution."""
    __tablename__ = "tps_plans"

    plan_id = Column(String(36), primary_key=True)
    brief_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approval_status = Column(String(20), default="pending", nullable=False)
    approved_by = Column(String(64), default="")
    approved_at = Column(DateTime, nullable=True)
    total_estimated_cost_usd = Column(Float, default=0.0)
    total_actual_cost_usd = Column(Float, default=0.0)
    plan_json = Column(JSON, nullable=True)  # Full PresentationPlan serialized

    assets = relationship("AssetRecord", back_populates="plan")


class AssetRecord(Base):
    """A generated visual asset."""
    __tablename__ = "tps_assets"

    asset_id = Column(String(36), primary_key=True)
    plan_id = Column(String(36), ForeignKey("tps_plans.plan_id"), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    generator = Column(String(40), nullable=False)
    title = Column(String(256), default="")
    status = Column(String(20), default="queued", nullable=False)
    output_path = Column(Text, default="")
    content_hash = Column(String(64), default="")
    estimated_cost_usd = Column(Float, default=0.0)
    actual_cost_usd = Column(Float, default=0.0)
    generation_time_sec = Column(Float, default=0.0)
    qc_status = Column(String(40), default="pending_human_analyst_qc_review")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    plan = relationship("PlanRecord", back_populates="assets")


class ProvenanceRecord(Base):
    """Append-only provenance ledger for generation events."""
    __tablename__ = "tps_provenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(36), ForeignKey("tps_assets.asset_id"), nullable=False, index=True)
    plan_id = Column(String(36), nullable=False, index=True)
    brief_id = Column(String(64), nullable=False, index=True)
    kind = Column(String(20), nullable=False)
    generator = Column(String(40), nullable=False)
    model_used = Column(String(80), default="")
    provider = Column(String(40), default="")
    estimated_cost_usd = Column(Float, default=0.0)
    actual_cost_usd = Column(Float, default=0.0)
    generation_time_sec = Column(Float, default=0.0)
    input_hash = Column(String(64), default="")
    output_hash = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    qc_status = Column(String(40), default="pending_human_analyst_qc_review")
    metadata_json = Column(JSON, nullable=True)


class SourceEventRecord(Base):
    """Structured intelligence events for charting and map overlays.

    Analogous to GDELT-style records. Schema: event_id, timestamp,
    event_type, location, actors, source_rating, confidence, source_doc_id.
    """
    __tablename__ = "tps_source_events"

    event_id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_name = Column(String(128), default="")
    actors = Column(JSON, nullable=True)  # list of actor names
    source_rating = Column(String(10), default="")  # NATO Admiralty
    confidence = Column(String(20), default="")  # Kent band
    source_doc_id = Column(String(64), default="", index=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class IndicatorHistoryRecord(Base):
    """I&W indicator time series across successive TREVOR assessments."""
    __tablename__ = "tps_indicator_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_name = Column(String(128), nullable=False, index=True)
    brief_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Text, default="")
    trigger = Column(Text, default="")
    signal = Column(Text, default="")
    kent_band = Column(String(20), default="")
    pct_range_low = Column(Integer, nullable=True)
    pct_range_high = Column(Integer, nullable=True)
    status = Column(String(20), default="active")  # active/triggered/dismissed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
