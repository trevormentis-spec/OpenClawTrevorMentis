#!/usr/bin/env python3
"""Custom Skill Writer — Proposes new skills when no ClawHub skill exists.

Trevor proposes new skill design with inputs/outputs/dependencies/security model.
Drafts SKILL.md and implementation scaffold.

ALL custom skills require principal review before installation — hard runtime gate.
Rate limit: maximum 1 custom skill proposal per week.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


WORKSPACE = Path(__file__).resolve().parent.parent
CUSTOM_PROPOSALS_LOG = WORKSPACE / "memory" / "custom-skill-proposals.jsonl"
WEEKLY_LIMIT = 1


@dataclass
class CustomSkillProposal:
    """A proposed custom skill for principal review."""
    skill_name: str
    description: str
    inputs: list[str]
    outputs: list[str]
    dependencies: list[str]
    security_model: str  # Description of security boundaries
    touches_network: bool
    touches_credentials: bool
    touches_filesystem_outside_workspace: bool
    estimated_complexity: str  # "simple" | "moderate" | "complex"
    capability_gap_addressed: str
    skill_md_draft: str
    implementation_notes: str
    principal_approved: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _count_proposals_this_week() -> int:
    """Count custom skill proposals in current ISO week."""
    if not CUSTOM_PROPOSALS_LOG.exists():
        return 0
    current_week = time.strftime("%Y-W%W", time.gmtime())
    count = 0
    with open(CUSTOM_PROPOSALS_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("timestamp", "")
                if ts[:10]:
                    t = time.strptime(ts[:10], "%Y-%m-%d")
                    week = time.strftime("%Y-W%W", t)
                    if week == current_week:
                        count += 1
            except (json.JSONDecodeError, ValueError):
                continue
    return count


def propose_custom_skill(
    skill_name: str,
    description: str,
    inputs: list[str],
    outputs: list[str],
    dependencies: list[str],
    security_model: str,
    touches_network: bool = False,
    touches_credentials: bool = False,
    touches_filesystem: bool = False,
    estimated_complexity: str = "moderate",
    capability_gap: str = "",
    skill_md_draft: str = "",
    implementation_notes: str = "",
) -> Optional[CustomSkillProposal]:
    """
    Propose a custom skill for principal review.

    Returns the proposal if within rate limit, None if rate-limited.
    """
    if _count_proposals_this_week() >= WEEKLY_LIMIT:
        return None

    proposal = CustomSkillProposal(
        skill_name=skill_name,
        description=description,
        inputs=inputs,
        outputs=outputs,
        dependencies=dependencies,
        security_model=security_model,
        touches_network=touches_network,
        touches_credentials=touches_credentials,
        touches_filesystem_outside_workspace=touches_filesystem,
        estimated_complexity=estimated_complexity,
        capability_gap_addressed=capability_gap,
        skill_md_draft=skill_md_draft,
        implementation_notes=implementation_notes,
    )

    CUSTOM_PROPOSALS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_PROPOSALS_LOG, "a") as f:
        f.write(json.dumps(asdict(proposal)) + "\n")

    return proposal


def get_pending_proposals() -> list[dict]:
    """Get custom skill proposals awaiting principal approval."""
    if not CUSTOM_PROPOSALS_LOG.exists():
        return []
    pending = []
    with open(CUSTOM_PROPOSALS_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if not entry.get("principal_approved", False):
                    pending.append(entry)
            except json.JSONDecodeError:
                continue
    return pending
