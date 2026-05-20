"""TPS API Routes — all REST endpoints.

Endpoints:
  POST /api/ingest         — Upload a TREVOR brief JSON
  POST /api/plan           — Generate a presentation plan from a brief
  POST /api/plan/approve   — Approve a plan for execution
  POST /api/execute        — Execute an approved plan
  GET  /api/plan/{plan_id} — Get plan status and details
  GET  /api/assets/{asset_id} — Get asset status and provenance
  GET  /api/generators     — List available generators
  GET  /api/health         — Health check
  GET  /api/cost/estimate  — Estimate cost for a plan
"""
from __future__ import annotations

import os
import json
import tempfile
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.schemas import (
    PresentationPlan,
    AssetSpec,
    AssetKind,
    DeliverableKind,
    ApprovalStatus,
    QCStatus,
)
from core.ingest import ingest_json
from core.planner import plan_from_brief
from core.cost_estimator import estimate_plan, check_budget_headroom
from core.approval_gate import auto_approve_if_cheap
from core.orchestrator import (
    execute_plan,
    list_generators,
    get_generator,
    ExecutionResult,
)
from core.config import get_config
from core.provenance import read_provenance

router = APIRouter(prefix="/api", tags=["tps"])


# ── Request/Response Models ─────────────────────────────────────────────────

class IngestRequest(BaseModel):
    brief_json: dict


class IngestResponse(BaseModel):
    brief_id: str
    title: str
    sections_count: int
    judgments_count: int


class PlanRequest(BaseModel):
    brief_json: dict
    deliverables: list[str] = Field(default=["pdf"])
    max_assets: int = Field(default=8, ge=1, le=20)


class PlanResponse(BaseModel):
    plan_id: str
    brief_id: str
    assets: list[dict]
    deliverables: list[str]
    total_estimated_cost_usd: float
    total_estimated_time_sec: float
    approval_status: str
    requires_approval: bool


class ApproveRequest(BaseModel):
    plan_json: dict
    approved_by: str = "api_user"


class ExecuteRequest(BaseModel):
    plan_json: dict
    output_dir: Optional[str] = None


class ExecuteResponse(BaseModel):
    success_count: int
    failure_count: int
    total_cost_usd: float
    total_time_sec: float
    outputs: dict[str, str]
    errors: dict[str, str]


class CostEstimateRequest(BaseModel):
    plan_json: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    generators_count: int


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        generators_count=len(list_generators()),
    )


@router.get("/generators")
async def get_generators():
    """List all registered generators with availability."""
    gens = []
    for name in list_generators():
        gen = get_generator(name)
        gens.append({
            "name": name,
            "supported_kinds": gen.supported_kinds if gen else [],
            "available": gen.is_available() if gen else False,
        })
    return {"generators": gens}


@router.post("/ingest", response_model=IngestResponse)
async def ingest_brief(req: IngestRequest):
    """Parse a TREVOR brief JSON into structured form."""
    try:
        brief = ingest_json(req.brief_json)
        return IngestResponse(
            brief_id=brief.brief_id,
            title=brief.title,
            sections_count=len(brief.sections),
            judgments_count=len(brief.headline_judgments),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan", response_model=PlanResponse)
async def create_plan(req: PlanRequest):
    """Generate a presentation plan from a brief."""
    try:
        brief = ingest_json(req.brief_json)
        plan = plan_from_brief(
            brief,
            deliverables=req.deliverables,
            max_assets=req.max_assets,
        )
        cost_est = estimate_plan(plan)

        return PlanResponse(
            plan_id=plan.plan_id,
            brief_id=plan.brief_id,
            assets=[
                {
                    "asset_id": a.asset_id,
                    "kind": a.kind.value,
                    "generator": a.generator,
                    "title": a.title,
                    "estimated_cost_usd": a.estimated_cost_usd,
                }
                for a in plan.assets
            ],
            deliverables=[d.value for d in plan.deliverables],
            total_estimated_cost_usd=cost_est.total_cost_usd,
            total_estimated_time_sec=cost_est.total_time_sec,
            approval_status=plan.approval_status.value,
            requires_approval=cost_est.requires_approval,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plan/approve")
async def approve_plan(req: ApproveRequest):
    """Approve a plan for execution."""
    try:
        plan = PresentationPlan(**req.plan_json)
        plan.approval_status = ApprovalStatus.APPROVED
        plan.approved_by = req.approved_by

        return {
            "plan_id": plan.plan_id,
            "approval_status": plan.approval_status.value,
            "approved_by": plan.approved_by,
            "plan": plan.model_dump(mode="json"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest):
    """Execute an approved plan."""
    try:
        plan = PresentationPlan(**req.plan_json)
        config = get_config()
        output_dir = req.output_dir or config.output_dir

        result = execute_plan(plan, output_dir)

        return ExecuteResponse(
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_cost_usd=result.total_cost_usd,
            total_time_sec=result.total_time_sec,
            outputs=result.outputs,
            errors=result.errors,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost/estimate")
async def cost_estimate(req: CostEstimateRequest):
    """Estimate cost for a plan without executing."""
    try:
        plan = PresentationPlan(**req.plan_json)
        est = estimate_plan(plan)
        headroom = check_budget_headroom(est.total_cost_usd)

        return {
            "plan_id": plan.plan_id,
            "total_cost_usd": est.total_cost_usd,
            "total_time_sec": est.total_time_sec,
            "requires_approval": est.requires_approval,
            "expensive_assets": est.expensive_assets,
            "stale_pricing_warnings": est.stale_pricing_warnings,
            "budget_headroom": headroom,
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "generator": a.generator,
                    "estimated_cost_usd": a.estimated_cost_usd,
                    "estimated_time_sec": a.estimated_time_sec,
                }
                for a in est.assets
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provenance")
async def get_provenance(limit: int = 50):
    """Read recent provenance records."""
    try:
        records = read_provenance(limit=limit)
        return {"records": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
