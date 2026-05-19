#!/usr/bin/env python3
"""Skill Discovery — Periodically scan ClawHub for new relevant skills.

Runs weekly. Matches skills to identified capability gaps.
Proposes skills to principal with security rating + use case.
Principal approval required before install (hard gate).

Rate limit: maximum 3 skill discovery proposals per week.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


WORKSPACE = Path(__file__).resolve().parent.parent
PROPOSALS_LOG = WORKSPACE / "memory" / "skill-proposals.jsonl"
INSTALLS_LOG = WORKSPACE / "memory" / "skill-installs.jsonl"
GAPS_PATH = WORKSPACE / "analyst" / "meta" / "capability_gaps.json"
WEEKLY_LIMIT = 3


@dataclass
class SkillProposal:
    """A proposed skill for principal review."""
    skill_id: str
    source: str  # "clawhub" | "custom"
    name: str
    description: str
    security_rating: str  # "safe" | "review_required" | "dangerous"
    use_case: str
    capability_gap_addressed: str
    touches_network: bool = False
    touches_credentials: bool = False
    touches_filesystem_outside_workspace: bool = False
    principal_approved: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _count_proposals_this_week() -> int:
    """Count proposals made in the current ISO week."""
    if not PROPOSALS_LOG.exists():
        return 0
    current_week = time.strftime("%Y-W%W", time.gmtime())
    count = 0
    with open(PROPOSALS_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("timestamp", "")
                if ts[:10]:
                    # Parse date to check same week
                    t = time.strptime(ts[:10], "%Y-%m-%d")
                    week = time.strftime("%Y-W%W", t)
                    if week == current_week:
                        count += 1
            except (json.JSONDecodeError, ValueError):
                continue
    return count


def _assess_security(skill_meta: dict) -> str:
    """Assess security rating for a skill."""
    touches_net = skill_meta.get("touches_network", False)
    touches_creds = skill_meta.get("touches_credentials", False)
    touches_fs = skill_meta.get("touches_filesystem_outside_workspace", False)

    if touches_creds or touches_fs:
        return "review_required"
    if touches_net:
        return "review_required"
    return "safe"


def propose_skill(
    skill_id: str,
    name: str,
    description: str,
    source: str = "clawhub",
    use_case: str = "",
    capability_gap: str = "",
    touches_network: bool = False,
    touches_credentials: bool = False,
    touches_filesystem: bool = False,
) -> Optional[SkillProposal]:
    """
    Propose a skill for principal review.

    Returns the proposal if within rate limit, None if rate-limited.
    """
    if _count_proposals_this_week() >= WEEKLY_LIMIT:
        return None

    security = _assess_security({
        "touches_network": touches_network,
        "touches_credentials": touches_credentials,
        "touches_filesystem_outside_workspace": touches_filesystem,
    })

    proposal = SkillProposal(
        skill_id=skill_id,
        source=source,
        name=name,
        description=description,
        security_rating=security,
        use_case=use_case,
        capability_gap_addressed=capability_gap,
        touches_network=touches_network,
        touches_credentials=touches_credentials,
        touches_filesystem_outside_workspace=touches_filesystem,
    )

    PROPOSALS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROPOSALS_LOG, "a") as f:
        f.write(json.dumps(asdict(proposal)) + "\n")

    return proposal


def record_install(
    skill_id: str,
    source: str,
    security_rating: str,
    principal_approval_timestamp: str,
) -> None:
    """Record a skill installation (after principal approval)."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill_id": skill_id,
        "source": source,
        "security_rating_at_install": security_rating,
        "principal_approval_timestamp": principal_approval_timestamp,
    }
    INSTALLS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(INSTALLS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_pending_proposals() -> list[dict]:
    """Get proposals awaiting principal approval."""
    if not PROPOSALS_LOG.exists():
        return []
    pending = []
    with open(PROPOSALS_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if not entry.get("principal_approved", False):
                    pending.append(entry)
            except json.JSONDecodeError:
                continue
    return pending
