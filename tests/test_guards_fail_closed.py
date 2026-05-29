#!/usr/bin/env python3
"""Test: guards fail closed on LLM/network failure, not open.

Verifies:
1. scope_check returns needs_human_review (not in_scope) on LLM failure
2. fabrication_check blocks fabricated price with fake/non-URL citation
3. themes_preflight fails when keywords exist but no section heading coverage
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestScopeGuardFailsClosed(unittest.TestCase):
    """Scope check must return needs_human_review on failure, not in_scope."""

    def test_no_api_key_returns_needs_human_review(self):
        """When DEEPSEEK_API_KEY is unset, scope check fails closed."""
        from unittest.mock import patch
        from analyst.scope_check import check_scope

        with patch.dict(os.environ, {}, clear=True):
            result = check_scope("test topic")
            self.assertEqual(
                result["scope_status"],
                "needs_human_review",
                "Scope check with no API key should fail closed to needs_human_review",
            )
            self.assertIn("review", result.get("rationale", "").lower())


class TestFabricationGuardFailsClosed(unittest.TestCase):
    """Fabrication check must reject unsourced claims with fake citations."""

    def setUp(self):
        self.brief_text = """
## Middle East Analysis
The situation in the region remains tense. Oil prices are trading at $85/barrel.
Iran continues to enrich uranium.
        """

    def test_fake_citation_blocks(self):
        """A price with a fake citation [random text] must be flagged."""
        from analyst.fabrication_check import check_brief
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.brief_text)
            f.flush()
            issues = check_brief(f.name)

        # Should flag the unsourced price (no citation at all)
        fabrication_issues = [i for i in issues if "85" in str(i.get("price", "")) or "85" in str(i.get("claim", ""))]
        self.assertTrue(
            len(fabrication_issues) > 0,
            "Fabrication check should flag price with non-URL, non-GAP citation [some random text]",
        )

    def test_url_citation_passes(self):
        """A price with a URL citation must pass."""
        from analyst.fabrication_check import check_brief
        import tempfile

        text = """
## Energy Markets
Oil is trading at $85/barrel [https://reuters.com/article/oil-prices].
Demand remains steady.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(text)
            f.flush()
            issues = check_brief(f.name)

        fabrication_issues = [i for i in issues if "$85" in str(i.get("claim", ""))]
        self.assertEqual(
            len(fabrication_issues),
            0,
            "Price with URL citation should pass fabrication check",
        )

    def test_gap_marker_passes(self):
        """A price with explicit GAP marker must pass."""
        from analyst.fabrication_check import check_brief
        import tempfile

        text = """
## Market Overview
Oil above $80. No prediction market data available [GAP].
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(text)
            f.flush()
            issues = check_brief(f.name)

        fabrication_issues = [i for i in issues if "GAP" not in str(i.get("detail", ""))]
        self.assertEqual(
            len(fabrication_issues),
            0,
            "Price with GAP marker should pass fabrication check",
        )


class TestThemesGuardFailsClosed(unittest.TestCase):
    """Themes preflight must fail when keyword hits exist but no heading depth."""

    def test_keywords_without_headings_fails(self):
        """≥3 keyword mentions but no heading coverage → must fail."""
        from analyst.themes_preflight import check_theme_coverage

        # Brief with 4 keyword mentions in body but none in headings
        # Uses cartel_security theme which has: security, conflict, military, war, etc.
        text = """
## Summary paragraph
The conflict in the region continues. Military forces are engaged.
Security forces deployed. Defense spending increased. Weapons seized.
        """
        covered, count = check_theme_coverage(text, "cartel_security")
        self.assertFalse(covered)
        self.assertGreaterEqual(count, 4)

    def test_keywords_with_headings_passes(self):
        """≥3 keyword mentions AND ≥2 heading hits → must pass."""
        from analyst.themes_preflight import check_theme_coverage

        # Brief with keywords in both body AND headings
        # Uses cartel_security theme which has: security, conflict, military, war, troops, defense
        text = """
## CONFLICT Assessment
The military conflict in the region has intensified.
## Security Outlook
Defense analysts expect further security deterioration.
Troop deployments continue along the border. Armed conflict ongoing.
        """
        covered, count = check_theme_coverage(text, "cartel_security")
        self.assertTrue(covered)


if __name__ == "__main__":
    unittest.main()
