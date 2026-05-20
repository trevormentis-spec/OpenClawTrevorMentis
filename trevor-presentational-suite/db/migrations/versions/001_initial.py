"""001 — Initial TPS schema: plans, assets, provenance, events, indicators.

Revision ID: 001
Revises: None
Create Date: 2026-05-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tps_plans",
        sa.Column("plan_id", sa.String(36), primary_key=True),
        sa.Column("brief_id", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("approval_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("approved_by", sa.String(64), server_default=""),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("total_estimated_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("total_actual_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("plan_json", sa.JSON, nullable=True),
    )

    op.create_table(
        "tps_assets",
        sa.Column("asset_id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("tps_plans.plan_id"), nullable=False, index=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("generator", sa.String(40), nullable=False),
        sa.Column("title", sa.String(256), server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("output_path", sa.Text, server_default=""),
        sa.Column("content_hash", sa.String(64), server_default=""),
        sa.Column("estimated_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("actual_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("generation_time_sec", sa.Float, server_default="0.0"),
        sa.Column("qc_status", sa.String(40), server_default="pending_human_analyst_qc_review"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("metadata_json", sa.JSON, nullable=True),
    )

    op.create_table(
        "tps_provenance",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("tps_assets.asset_id"), nullable=False, index=True),
        sa.Column("plan_id", sa.String(36), nullable=False, index=True),
        sa.Column("brief_id", sa.String(64), nullable=False, index=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("generator", sa.String(40), nullable=False),
        sa.Column("model_used", sa.String(80), server_default=""),
        sa.Column("provider", sa.String(40), server_default=""),
        sa.Column("estimated_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("actual_cost_usd", sa.Float, server_default="0.0"),
        sa.Column("generation_time_sec", sa.Float, server_default="0.0"),
        sa.Column("input_hash", sa.String(64), server_default=""),
        sa.Column("output_hash", sa.String(64), server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("qc_status", sa.String(40), server_default="pending_human_analyst_qc_review"),
        sa.Column("metadata_json", sa.JSON, nullable=True),
    )

    op.create_table(
        "tps_source_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("location_lat", sa.Float, nullable=True),
        sa.Column("location_lon", sa.Float, nullable=True),
        sa.Column("location_name", sa.String(128), server_default=""),
        sa.Column("actors", sa.JSON, nullable=True),
        sa.Column("source_rating", sa.String(10), server_default=""),
        sa.Column("confidence", sa.String(20), server_default=""),
        sa.Column("source_doc_id", sa.String(64), server_default="", index=True),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "tps_indicator_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("indicator_name", sa.String(128), nullable=False, index=True),
        sa.Column("brief_id", sa.String(64), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("value", sa.Text, server_default=""),
        sa.Column("trigger", sa.Text, server_default=""),
        sa.Column("signal", sa.Text, server_default=""),
        sa.Column("kent_band", sa.String(20), server_default=""),
        sa.Column("pct_range_low", sa.Integer, nullable=True),
        sa.Column("pct_range_high", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tps_indicator_history")
    op.drop_table("tps_source_events")
    op.drop_table("tps_provenance")
    op.drop_table("tps_assets")
    op.drop_table("tps_plans")
