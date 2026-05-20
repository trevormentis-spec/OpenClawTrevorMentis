"""TPS fal.ai Client — unified SDK for image and video generation.

Single gateway for Flux 2 Pro, Ideogram V3, Recraft V4, Imagen 4, Kling 3.0.
Uses httpx for synchronous HTTP calls with retry via tenacity.
"""
from __future__ import annotations

import os
import time
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


FAL_BASE_URL = "https://queue.fal.run"
FAL_RESULT_URL = "https://queue.fal.run"


def _get_api_key() -> str:
    key = os.environ.get("FAL_KEY", "")
    if not key:
        from core.config import TPS_ROOT
        env_path = TPS_ROOT.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("FAL_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"')
                    break
    return key


def is_available() -> bool:
    """Check if fal.ai credentials are set."""
    return bool(_get_api_key())


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
)
def submit_and_poll(
    model_id: str,
    payload: dict,
    timeout_sec: int = 120,
) -> dict:
    """Submit a job to fal.ai, poll for completion, return result.

    fal.ai queue API:
    1. POST /{model_id} → {"request_id": "..."}
    2. GET /{model_id}/requests/{request_id}/status → poll until COMPLETED
    3. GET /{model_id}/requests/{request_id} → result with image URLs
    """
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("FAL_KEY not set")

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout_sec) as client:
        # Submit
        submit_url = f"{FAL_BASE_URL}/{model_id}"
        resp = client.post(submit_url, json=payload, headers=headers)
        resp.raise_for_status()
        submit_data = resp.json()
        request_id = submit_data.get("request_id", "")

        if not request_id:
            # Synchronous response (some models return immediately)
            return submit_data

        # Poll for completion
        status_url = f"{FAL_BASE_URL}/{model_id}/requests/{request_id}/status"
        result_url = f"{FAL_BASE_URL}/{model_id}/requests/{request_id}"

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            status_resp = client.get(status_url, headers=headers)
            status_resp.raise_for_status()
            status_data = status_resp.json()
            status = status_data.get("status", "")

            if status == "COMPLETED":
                result_resp = client.get(result_url, headers=headers)
                result_resp.raise_for_status()
                return result_resp.json()
            elif status in ("FAILED", "CANCELLED"):
                error = status_data.get("error", "Unknown error")
                raise RuntimeError(f"fal.ai job {request_id} {status}: {error}")

            time.sleep(2)

        raise TimeoutError(f"fal.ai job {request_id} timed out after {timeout_sec}s")


def download_image(url: str, output_path: str) -> bytes:
    """Download an image from a fal.ai result URL."""
    with httpx.Client(timeout=60) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.content
        with open(output_path, "wb") as f:
            f.write(data)
        return data
