"""TPS Webhook Handlers — receive callbacks from async providers.

Some providers (HeyGen, fal.ai) support webhook callbacks instead of polling.
This module provides webhook endpoints for those callbacks.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from core.provenance import build_provenance, record_provenance

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@webhook_router.post("/fal/{request_id}")
async def fal_webhook(request_id: str, request: Request):
    """Handle fal.ai completion webhook.

    fal.ai can POST results to a webhook URL instead of requiring polling.
    This endpoint receives the completed result and stores it.
    """
    try:
        body = await request.json()
        status = body.get("status", "")
        logger.info(f"fal.ai webhook: request_id={request_id}, status={status}")

        if status == "COMPLETED":
            # Store result for later retrieval
            _store_webhook_result("fal", request_id, body)
            return {"ok": True, "request_id": request_id}
        elif status in ("FAILED", "CANCELLED"):
            error = body.get("error", "Unknown")
            logger.error(f"fal.ai job failed: {request_id}: {error}")
            _store_webhook_result("fal", request_id, body)
            return {"ok": True, "request_id": request_id, "status": status}
        else:
            return {"ok": True, "request_id": request_id, "status": "ignored"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@webhook_router.post("/heygen/{video_id}")
async def heygen_webhook(video_id: str, request: Request):
    """Handle HeyGen video completion webhook."""
    try:
        body = await request.json()
        status = body.get("data", {}).get("status", body.get("status", ""))
        logger.info(f"HeyGen webhook: video_id={video_id}, status={status}")

        _store_webhook_result("heygen", video_id, body)
        return {"ok": True, "video_id": video_id, "status": status}

    except Exception as e:
        logger.error(f"HeyGen webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Webhook Result Storage ──────────────────────────────────────────────────

_webhook_results: dict[str, dict] = {}


def _store_webhook_result(provider: str, job_id: str, data: dict):
    """Store webhook result in memory for retrieval by generators."""
    key = f"{provider}:{job_id}"
    _webhook_results[key] = {
        "provider": provider,
        "job_id": job_id,
        "data": data,
        "received_at": datetime.utcnow().isoformat(),
    }


def get_webhook_result(provider: str, job_id: str) -> dict | None:
    """Retrieve a stored webhook result."""
    key = f"{provider}:{job_id}"
    return _webhook_results.get(key)


def clear_webhook_result(provider: str, job_id: str):
    """Clear a consumed webhook result."""
    key = f"{provider}:{job_id}"
    _webhook_results.pop(key, None)
