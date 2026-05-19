#!/usr/bin/env python3
"""Capability Gap — Track and categorize capability gaps.

When Trevor lacks a capability, it's tracked here with categorization
and remediation proposal.

Categories:
- skill_available_on_clawhub: ClawHub has a skill for this
- custom_skill_needed: No existing skill, Trevor needs to write one
- external_service_needed: Requires a paid external service
- principal_decision_required: Needs principal input to resolve
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


WORKSPACE = Path(__file__).resolve().parent.parent
GAPS_PATH = WORKSPACE / "analyst" / "meta" / "capability_gaps.json"


@dataclass
class CapabilityGap:
    """A tracked capability gap."""
    id: str
    description: str
    category: str  # skill_available_on_clawhub | custom_skill_needed | external_service_needed | principal_decision_required
    discovered: str
    topic_context: str = ""
    remediation_proposal: str = ""
    status: str = "open"  # open | proposed | resolved | wont_fix
    resolved_by: str = ""  # skill_id or action taken
    resolved_at: str = ""

    def __post_init__(self):
        if not self.discovered:
            self.discovered = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_gaps() -> list[CapabilityGap]:
    """Load all capability gaps."""
    if not GAPS_PATH.exists():
        return []
    try:
        data = json.loads(GAPS_PATH.read_text())
        if isinstance(data, list):
            return [CapabilityGap(**g) for g in data]
        elif isinstance(data, dict) and "gaps" in data:
            return [CapabilityGap(**g) for g in data["gaps"]]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def save_gaps(gaps: list[CapabilityGap]) -> None:
    """Save capability gaps to file."""
    GAPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"gaps": [asdict(g) for g in gaps],
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    GAPS_PATH.write_text(json.dumps(data, indent=2))


def add_gap(
    description: str,
    category: str,
    topic_context: str = "",
    remediation_proposal: str = "",
) -> CapabilityGap:
    """Add a new capability gap."""
    gaps = load_gaps()
    gap_id = f"gap-{int(time.time())}"
    gap = CapabilityGap(
        id=gap_id,
        description=description,
        category=category,
        topic_context=topic_context,
        remediation_proposal=remediation_proposal,
        discovered=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    gaps.append(gap)
    save_gaps(gaps)
    return gap


def resolve_gap(gap_id: str, resolved_by: str) -> bool:
    """Mark a capability gap as resolved."""
    gaps = load_gaps()
    for gap in gaps:
        if gap.id == gap_id:
            gap.status = "resolved"
            gap.resolved_by = resolved_by
            gap.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            save_gaps(gaps)
            return True
    return False


def get_open_gaps() -> list[CapabilityGap]:
    """Get all open capability gaps."""
    return [g for g in load_gaps() if g.status == "open"]


def get_gaps_by_category(category: str) -> list[CapabilityGap]:
    """Get open gaps of a specific category."""
    return [g for g in get_open_gaps() if g.category == category]
