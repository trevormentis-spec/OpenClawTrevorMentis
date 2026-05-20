# GATE_EXEMPT: Test file — references model strings for testing self-improvement. Does not make API calls.
#!/usr/bin/env python3
"""Tests for self-improvement mechanisms.

Tests:
- Skill proposal workflow
- Principal approval gate enforcement
- Forum monitor entry/synthesis logging
- Rate limit enforcement
- Capability gap tracking
- Custom skill proposals
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyst.skill_discovery import (
    propose_skill, record_install, get_pending_proposals,
    SkillProposal, PROPOSALS_LOG, INSTALLS_LOG, WEEKLY_LIMIT
)
from analyst.forum_monitor import (
    log_entry, record_synthesis, get_recent_entries, get_monitor_targets,
    ForumEntry, ForumSynthesis, FORUM_LOG, SYNTHESIS_LOG
)
from analyst.capability_gap import (
    add_gap, resolve_gap, get_open_gaps, get_gaps_by_category,
    load_gaps, save_gaps, CapabilityGap, GAPS_PATH
)
from analyst.custom_skill_writer import (
    propose_custom_skill, get_pending_proposals as get_custom_pending,
    CustomSkillProposal, CUSTOM_PROPOSALS_LOG
)


class TempFileContext:
    """Temporarily redirect log files to temp directory."""
    def __init__(self):
        self.tmpdir = tempfile.mkdtemp()
        self.originals = {}

    def patch(self, module, attr_name):
        """Redirect a module-level Path to temp dir."""
        original = getattr(module, attr_name)
        self.originals[(module, attr_name)] = original
        new_path = Path(self.tmpdir) / original.name
        setattr(module, attr_name, new_path)

    def restore(self):
        """Restore all original paths."""
        for (module, attr_name), original in self.originals.items():
            setattr(module, attr_name, original)
        shutil.rmtree(self.tmpdir, ignore_errors=True)


def test_skill_proposal_basic():
    """Test basic skill proposal creation."""
    import analyst.skill_discovery as sd
    ctx = TempFileContext()
    ctx.patch(sd, "PROPOSALS_LOG")

    try:
        proposal = propose_skill(
            skill_id="clawhub:rss-monitor",
            name="RSS Monitor",
            description="Monitors RSS feeds for new articles",
            use_case="Automated source ingestion",
            capability_gap="No RSS monitoring capability",
        )
        ok1 = proposal is not None
        ok2 = proposal.security_rating == "safe"  # No network/creds/fs flags
        ok3 = proposal.principal_approved == False

        # Check logged
        ok4 = sd.PROPOSALS_LOG.exists()
        if ok4:
            entries = sd.PROPOSALS_LOG.read_text().strip().split("\n")
            ok4 = len(entries) == 1

        passed = sum([ok1, ok2, ok3, ok4])
        for name, ok in [("created", ok1), ("safe_rating", ok2), ("not_approved", ok3), ("logged", ok4)]:
            if not ok:
                print(f"  FAIL: {name}")
        print(f"[skill_proposal_basic] {passed}/4 passed")
        return passed == 4
    finally:
        ctx.restore()


def test_skill_proposal_security_rating():
    """Test security rating assessment."""
    import analyst.skill_discovery as sd
    ctx = TempFileContext()
    ctx.patch(sd, "PROPOSALS_LOG")

    try:
        # Network-touching skill
        p1 = propose_skill(
            skill_id="clawhub:web-scraper-pro",
            name="Web Scraper Pro",
            description="Advanced web scraping",
            touches_network=True,
        )
        ok1 = p1.security_rating == "review_required"

        # Credential-touching skill
        p2 = propose_skill(
            skill_id="clawhub:api-key-manager",
            name="API Key Manager",
            description="Manages API credentials",
            touches_credentials=True,
        )
        ok2 = p2.security_rating == "review_required"

        # Safe skill
        p3 = propose_skill(
            skill_id="clawhub:markdown-formatter",
            name="Markdown Formatter",
            description="Formats markdown documents",
        )
        ok3 = p3 is not None and p3.security_rating == "safe"

        passed = sum([ok1, ok2, ok3])
        for name, ok in [("network_review", ok1), ("creds_review", ok2), ("safe", ok3)]:
            if not ok:
                print(f"  FAIL: {name}")
        print(f"[security_rating] {passed}/3 passed")
        return passed == 3
    finally:
        ctx.restore()


def test_skill_proposal_rate_limit():
    """Test weekly rate limit enforcement."""
    import analyst.skill_discovery as sd
    ctx = TempFileContext()
    ctx.patch(sd, "PROPOSALS_LOG")

    try:
        # Fill up the weekly limit
        for i in range(WEEKLY_LIMIT):
            p = propose_skill(
                skill_id=f"clawhub:test-skill-{i}",
                name=f"Test Skill {i}",
                description=f"Test skill number {i}",
            )
            assert p is not None, f"Proposal {i} should succeed"

        # Next proposal should be rate-limited
        p_limited = propose_skill(
            skill_id="clawhub:one-too-many",
            name="One Too Many",
            description="Should be rate limited",
        )
        ok = p_limited is None
        if not ok:
            print(f"  FAIL: proposal should be rate-limited after {WEEKLY_LIMIT}")
        print(f"[rate_limit] {'PASS' if ok else 'FAIL'}")
        return ok
    finally:
        ctx.restore()


def test_skill_install_logging():
    """Test skill installation logging."""
    import analyst.skill_discovery as sd
    ctx = TempFileContext()
    ctx.patch(sd, "INSTALLS_LOG")

    try:
        record_install(
            skill_id="clawhub:rss-monitor",
            source="clawhub",
            security_rating="safe",
            principal_approval_timestamp="2026-05-19T20:00:00Z",
        )

        ok = sd.INSTALLS_LOG.exists()
        if ok:
            entry = json.loads(sd.INSTALLS_LOG.read_text().strip())
            ok = (entry.get("skill_id") == "clawhub:rss-monitor" and
                  entry.get("principal_approval_timestamp") == "2026-05-19T20:00:00Z")
        print(f"[install_logging] {'PASS' if ok else 'FAIL'}")
        return ok
    finally:
        ctx.restore()


def test_forum_entry_logging():
    """Test forum monitoring entry logging."""
    import analyst.forum_monitor as fm
    ctx = TempFileContext()
    ctx.patch(fm, "FORUM_LOG")

    try:
        entry = ForumEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            source="reddit_openclaw",
            title="New technique for agent memory management",
            url="https://reddit.com/r/openclaw/test",
            content_summary="Describes a novel approach to episodic memory pruning",
            relevance="high",
            category="technique",
        )
        log_entry(entry)

        ok1 = fm.FORUM_LOG.exists()
        entries = get_recent_entries(days=1)
        ok2 = len(entries) == 1
        ok3 = entries[0]["category"] == "technique" if entries else False

        passed = sum([ok1, ok2, ok3])
        print(f"[forum_entry_logging] {passed}/3 passed")
        return passed == 3
    finally:
        ctx.restore()


def test_forum_synthesis_rate_limit():
    """Test forum synthesis weekly rate limit."""
    import analyst.forum_monitor as fm
    ctx = TempFileContext()
    ctx.patch(fm, "SYNTHESIS_LOG")

    try:
        synthesis = ForumSynthesis(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            period_start="2026-05-12",
            period_end="2026-05-19",
            entries_reviewed=15,
            actionable_findings=[{"finding": "Test", "action": "None"}],
            skill_recommendations=["test-skill"],
            security_warnings=[],
            technique_improvements=["memory pruning"],
        )

        ok1 = record_synthesis(synthesis)
        ok2 = not record_synthesis(synthesis)  # Second should be rate-limited

        passed = sum([ok1, ok2])
        print(f"[forum_synthesis_rate_limit] {passed}/2 passed")
        return passed == 2
    finally:
        ctx.restore()


def test_monitor_targets():
    """Test monitor targets configuration."""
    targets = get_monitor_targets()
    ok1 = len(targets) >= 4
    ok2 = any(t["source"] == "reddit_openclaw" for t in targets)
    ok3 = any(t["source"] == "hn_ai_agents" for t in targets)
    ok4 = any(t["source"] == "moltbook" for t in targets)

    passed = sum([ok1, ok2, ok3, ok4])
    print(f"[monitor_targets] {passed}/4 passed")
    return passed == 4


def test_capability_gap_tracking():
    """Test capability gap add/resolve workflow."""
    import analyst.capability_gap as cg
    ctx = TempFileContext()
    ctx.patch(cg, "GAPS_PATH")

    try:
        gap1 = add_gap(
            description="Cannot ingest PDF tables",
            category="skill_available_on_clawhub",
            topic_context="semiconductor-supply-chain",
            remediation_proposal="Install pdf-table-extractor from ClawHub",
        )
        ok1 = gap1.status == "open"

        gap2 = add_gap(
            description="No satellite imagery source",
            category="external_service_needed",
            remediation_proposal="Subscribe to Planet or Maxar",
        )
        ok2 = len(get_open_gaps()) == 2

        ok3 = len(get_gaps_by_category("skill_available_on_clawhub")) == 1
        ok4 = len(get_gaps_by_category("external_service_needed")) == 1

        # Resolve one
        resolve_gap(gap1.id, "installed pdf-table-extractor v2.1")
        ok5 = len(get_open_gaps()) == 1

        passed = sum([ok1, ok2, ok3, ok4, ok5])
        for name, ok in [("gap_open", ok1), ("two_gaps", ok2), ("filter_clawhub", ok3),
                          ("filter_external", ok4), ("resolve", ok5)]:
            if not ok:
                print(f"  FAIL: {name}")
        print(f"[capability_gap] {passed}/5 passed")
        return passed == 5
    finally:
        ctx.restore()


def test_custom_skill_proposal():
    """Test custom skill proposal workflow."""
    import analyst.custom_skill_writer as csw
    ctx = TempFileContext()
    ctx.patch(csw, "CUSTOM_PROPOSALS_LOG")

    try:
        proposal = propose_custom_skill(
            skill_name="maritime-sanctions-checker",
            description="Cross-references vessel data with OFAC sanctions list",
            inputs=["vessel_name", "imo_number"],
            outputs=["sanctions_match", "risk_score"],
            dependencies=["urllib"],
            security_model="Network access to OFAC API only. No credential storage.",
            touches_network=True,
            capability_gap="Cannot check vessels against sanctions",
            skill_md_draft="# maritime-sanctions-checker\n...",
            implementation_notes="Use OFAC SDN list XML download",
        )
        ok1 = proposal is not None
        ok2 = proposal.touches_network == True

        # Check it shows in pending
        pending = get_custom_pending()
        ok3 = len(pending) == 1
        ok4 = pending[0]["principal_approved"] == False

        passed = sum([ok1, ok2, ok3, ok4])
        for name, ok in [("created", ok1), ("network_flag", ok2), ("pending", ok3), ("not_approved", ok4)]:
            if not ok:
                print(f"  FAIL: {name}")
        print(f"[custom_skill_proposal] {passed}/4 passed")
        return passed == 4
    finally:
        ctx.restore()


def test_custom_skill_rate_limit():
    """Test custom skill weekly rate limit."""
    import analyst.custom_skill_writer as csw
    ctx = TempFileContext()
    ctx.patch(csw, "CUSTOM_PROPOSALS_LOG")

    try:
        p1 = propose_custom_skill(
            skill_name="skill-1",
            description="First skill",
            inputs=[], outputs=[], dependencies=[],
            security_model="none",
        )
        ok1 = p1 is not None

        p2 = propose_custom_skill(
            skill_name="skill-2",
            description="Should be rate limited",
            inputs=[], outputs=[], dependencies=[],
            security_model="none",
        )
        ok2 = p2 is None  # Rate limited (1/week)

        passed = sum([ok1, ok2])
        print(f"[custom_skill_rate_limit] {passed}/2 passed")
        return passed == 2
    finally:
        ctx.restore()


def test_principal_approval_gate():
    """Test that no proposal is auto-approved."""
    import analyst.skill_discovery as sd
    import analyst.custom_skill_writer as csw
    ctx = TempFileContext()
    ctx.patch(sd, "PROPOSALS_LOG")
    ctx.patch(csw, "CUSTOM_PROPOSALS_LOG")

    try:
        # Regular skill proposal
        p1 = propose_skill(
            skill_id="clawhub:test",
            name="Test",
            description="Test skill",
        )
        ok1 = not p1.principal_approved

        # Custom skill proposal
        p2 = propose_custom_skill(
            skill_name="test-custom",
            description="Test custom",
            inputs=[], outputs=[], dependencies=[],
            security_model="none",
        )
        ok2 = not p2.principal_approved

        # Verify pending lists show unapproved
        ok3 = all(not p.get("principal_approved") for p in get_pending_proposals())
        ok4 = all(not p.get("principal_approved") for p in get_custom_pending())

        passed = sum([ok1, ok2, ok3, ok4])
        print(f"[principal_approval_gate] {passed}/4 passed")
        return passed == 4
    finally:
        ctx.restore()


def run_all():
    """Run all self-improvement tests."""
    print("=" * 60)
    print("Trevor v2 — Self-Improvement Tests")
    print("=" * 60)

    tests = [
        test_skill_proposal_basic,
        test_skill_proposal_security_rating,
        test_skill_proposal_rate_limit,
        test_skill_install_logging,
        test_forum_entry_logging,
        test_forum_synthesis_rate_limit,
        test_monitor_targets,
        test_capability_gap_tracking,
        test_custom_skill_proposal,
        test_custom_skill_rate_limit,
        test_principal_approval_gate,
    ]

    results = []
    for test_fn in tests:
        try:
            results.append(test_fn())
        except Exception as e:
            print(f"[{test_fn.__name__}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"TOTAL: {passed}/{total} test groups passed")
    if passed == total:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILURES: {total - passed} test groups failed")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
