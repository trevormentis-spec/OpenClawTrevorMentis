"""TPS API Server — FastAPI application with CORS, lifecycle, and error handling.

Run: uvicorn api.server:app --host 0.0.0.0 --port 8100
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure TPS modules are importable
TPS_ROOT = Path(__file__).resolve().parent.parent
if str(TPS_ROOT) not in sys.path:
    sys.path.insert(0, str(TPS_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.exceptions import (
    TPSError,
    ApprovalRequiredError,
    BudgetExceededError,
    PlanValidationError,
    GeneratorError,
)
from core.orchestrator import register_all_generators
from db.engine import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup
    register_all_generators()
    init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="Trevor Presentational Suite",
    description="REST API for TREVOR's visual content generation pipeline.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Replit preview and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error Handlers ──────────────────────────────────────────────────────────

@app.exception_handler(ApprovalRequiredError)
async def approval_required_handler(request: Request, exc: ApprovalRequiredError):
    return JSONResponse(
        status_code=402,
        content={"error": "approval_required", "detail": str(exc)},
    )


@app.exception_handler(BudgetExceededError)
async def budget_exceeded_handler(request: Request, exc: BudgetExceededError):
    return JSONResponse(
        status_code=402,
        content={"error": "budget_exceeded", "detail": str(exc)},
    )


@app.exception_handler(PlanValidationError)
async def plan_validation_handler(request: Request, exc: PlanValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "plan_validation_failed", "detail": str(exc)},
    )


@app.exception_handler(GeneratorError)
async def generator_error_handler(request: Request, exc: GeneratorError):
    return JSONResponse(
        status_code=500,
        content={"error": "generator_error", "detail": str(exc)},
    )


@app.exception_handler(TPSError)
async def tps_error_handler(request: Request, exc: TPSError):
    return JSONResponse(
        status_code=500,
        content={"error": "tps_error", "detail": str(exc)},
    )


# Import routes
from api.routes import router
app.include_router(router)
