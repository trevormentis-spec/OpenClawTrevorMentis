"""TPS Provenance — track which model produced what, when, at what cost.

Append-only JSONL ledger matching TREVOR's existing pattern
(analyst/cost_ledger.py → memory/cost-ledger.jsonl).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schemas import AssetProvenance, QCStatus

TREVOR_ROOT = Path(__file__).resolve().parent.parent.parent
PROVENANCE_LOG = TREVOR_ROOT / "memory" / "tps-provenance.jsonl"


def record_provenance(prov: AssetProvenance) -> None:
    """Append a provenance record to the JSONL ledger."""
    PROVENANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = prov.model_dump(mode="json")
    # Serialize datetime fields
    for key in ("created_at", "qc_timestamp"):
        if isinstance(entry.get(key), datetime):
            entry[key] = entry[key].isoformat()
    with open(PROVENANCE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_provenance(
    brief_id: str = "",
    plan_id: str = "",
    asset_id: str = "",
) -> list[AssetProvenance]:
    """Load provenance records filtered by brief, plan, or asset ID."""
    if not PROVENANCE_LOG.exists():
        return []

    results = []
    with open(PROVENANCE_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if brief_id and entry.get("brief_id") != brief_id:
                continue
            if plan_id and entry.get("plan_id") != plan_id:
                continue
            if asset_id and entry.get("asset_id") != asset_id:
                continue

            try:
                results.append(AssetProvenance(**entry))
            except Exception:
                continue

    return results


def stamp_qc_pending(prov: AssetProvenance) -> AssetProvenance:
    """Ensure PENDING HUMAN ANALYST QC REVIEW flag is set."""
    prov.qc_status = QCStatus.PENDING_REVIEW
    return prov


def hash_file(path: str) -> str:
    """SHA256 hash of a file."""
    h = hashlib.sha256()
    p = Path(path)
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def hash_data(data: bytes) -> str:
    """SHA256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def read_provenance(limit: int = 50) -> list[dict]:
    """Read recent provenance records as dicts (for API responses)."""
    if not PROVENANCE_LOG.exists():
        return []

    records = []
    with open(PROVENANCE_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Return most recent first
    return list(reversed(records[-limit:]))


def build_provenance(
    asset_id: str,
    plan_id: str,
    brief_id: str,
    kind: str,
    generator: str,
    model_used: str = "",
    provider: str = "",
    estimated_cost_usd: float = 0.0,
    actual_cost_usd: float = 0.0,
    generation_time_sec: float = 0.0,
    input_data: bytes = b"",
    output_path: str = "",
) -> AssetProvenance:
    """Build a complete provenance record with hashes and QC flag."""
    from .schemas import AssetKind

    output_hash = hash_file(output_path) if output_path else ""
    input_hash = hash_data(input_data) if input_data else ""

    prov = AssetProvenance(
        asset_id=asset_id,
        plan_id=plan_id,
        brief_id=brief_id,
        kind=AssetKind(kind),
        generator=generator,
        model_used=model_used,
        provider=provider,
        estimated_cost_usd=estimated_cost_usd,
        actual_cost_usd=actual_cost_usd,
        generation_time_sec=generation_time_sec,
        input_hash=input_hash,
        output_path=output_path,
        output_hash=output_hash,
        qc_status=QCStatus.PENDING_REVIEW,
    )
    return prov
