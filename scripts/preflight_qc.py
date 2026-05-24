#!/usr/bin/env python3
"""
Universal preflight QC — runs on any outgoing report before delivery.
Blocks delivery on CRITICAL failures, warns on MINOR issues.

Usage:
    from scripts.preflight_qc import check_report
    ok, issues = check_report(body, report_type="leo_brief")
    if not ok:
        print("BLOCKED:", issues)
        sys.exit(1)

Gate levels:
    CRITICAL — delivery blocked. Must fix before sending.
    WARN     — logged but delivery proceeds.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QCIssue:
    level: str        # CRITICAL, WARN
    category: str     # completeness, formatting, language, content
    detail: str


@dataclass
class QCResult:
    passed: bool
    issues: list[QCIssue] = field(default_factory=list)
    checked_at: str = ""

    def has_critical(self) -> bool:
        return any(i.level == "CRITICAL" for i in self.issues)

    def summary(self) -> str:
        if self.passed and not self.issues:
            return "✅ QC PASS — no issues"
        criticals = [i for i in self.issues if i.level == "CRITICAL"]
        warns = [i for i in self.issues if i.level == "WARN"]
        parts = []
        if criticals:
            parts.append(f"❌ {len(criticals)} CRITICAL")
        if warns:
            parts.append(f"⚠️ {len(warns)} WARN")
        if not parts:
            parts.append("✅ CLEAN")
        return " | ".join(parts)


def check_report(
    body: str,
    report_type: str = "generic",
    min_words: int = 50,
    max_empty_ratio: float = 0.9,
) -> QCResult:
    """
    Run preflight QC on a report body before delivery.

    Args:
        body: Full report text or HTML
        report_type: Label for logging (e.g. 'leo_brief', 'daily_brief', 'moltbook_post')
        min_words: Minimum word count before flagging
        max_empty_ratio: Max ratio of empty/placeholder lines allowed

    Returns QCResult with passed=True if no CRITICAL issues.
    """
    result = QCResult(passed=True, checked_at=datetime.now(timezone.utc).isoformat())
    issues = []

    # ── Gate 1: EMPTY or too short ──
    stripped = body.strip()
    if not stripped or len(stripped) < 10:
        issues.append(QCIssue("CRITICAL", "completeness", "Body is empty or under 10 chars"))
        result.passed = False
        result.issues = issues
        return result

    words = stripped.split()
    if len(words) < min_words:
        issues.append(QCIssue("CRITICAL", "completeness",
            f"Body too short: {len(words)} words (min {min_words})"))

    # ── Gate 2: ERROR/placeholder content ──
    error_patterns = [
        ("ERROR:", "Contains error message"),
        ("Traceback (most recent call last)", "Contains Python traceback"),
        ("MISSING", "Contains MISSING placeholder"),
        ("Error generating", "Contains error generation message"),
        ("[object Object]", "Contains JavaScript error string"),
        ("undefined", "Contains 'undefined' (possible JS error)"),
    ]
    # Conditional patterns
    if stripped.lower() in ("n/a", "n/a."):
        error_patterns.append(("N/A", "Entire body is N/A"))
    if stripped.lower() in ("null", "none", "nil"):
        error_patterns.append(("null", "Entire body is null/none"))
    for pattern, desc in error_patterns:
        if pattern and pattern in stripped:
            issues.append(QCIssue("CRITICAL", "content", desc))

    # ── Gate 3: Only contains data sources / no analysis ──
    analysis_indicators = [
        "executive summary", "analysis", "assessment", "signal", "trend",
        "what to watch", "bottom line", "recommend", "outlook", "forecast",
        "implication", "judgment", "probability", "likely", "unlikely",
    ]
    body_lower = stripped.lower()

    # Check if body is mostly data/sources — flag if >50% of lines are source attributions
    # AND no analysis indicators are present
    lines = [l for l in stripped.split("\n") if l.strip()]
    source_keywords = ["source:", "data source", "fcc opendata", "launch library",
                       "copernicus", "concentric", "• fcc", "• launch",
                       "• copernicus", "• spaceflight", "• concentr",
                       "• job board", "• itu", "deepseek v4 pro"]
    if lines:
        source_lines = sum(1 for l in lines if any(s in l.lower() for s in source_keywords))
        source_ratio = source_lines / len(lines)
        has_analysis = any(ind in body_lower for ind in analysis_indicators)
        if source_ratio > 0.5 and not has_analysis:
            issues.append(QCIssue("CRITICAL", "completeness",
                f"Report is {source_lines}/{len(lines)} source attributions ({source_ratio:.0%}) "
                "with no analysis content — likely missing LLM-generated analysis"))

    # Check if any analysis indicators are present
    has_analysis = any(ind in body_lower for ind in analysis_indicators)
    if not has_analysis and "data source" not in body_lower:
        # Only warn if it's not a pure data report
        pass  # Not necessarily a problem — some reports are data-only by design

    # ── Gate 4: Language check — no raw Chinese/CJK in English reports ──
    if report_type not in ("raw_data", "multilingual"):
        cjk_count = sum(1 for c in stripped if '\u4e00' <= c <= '\u9fff' or
                        '\u3040' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7af')
        if cjk_count > 20:
            issues.append(QCIssue("CRITICAL", "language",
                f"Report contains {cjk_count} CJK characters — likely wrong language. "
                "Expected English."))
        elif cjk_count > 5:
            issues.append(QCIssue("WARN", "language",
                f"Report contains {cjk_count} CJK characters — verify language is correct"))

    # ── Gate 5: HTML validity (for HTML reports) ──
    if stripped.startswith("<") and report_type not in ("plain_text",):
        if "<html" not in stripped.lower() and "<body" not in stripped.lower():
            issues.append(QCIssue("WARN", "formatting",
                "Looks like HTML fragment without <html>/<body> wrapper"))
        if stripped.count("<") != stripped.count(">"):
            issues.append(QCIssue("CRITICAL", "formatting",
                f"Mismatched HTML tags: {stripped.count('<')} < vs {stripped.count('>')} >"))

    # ── Gate 6: Duplicate/copy-paste detection ──
    # Check if first 200 chars of body appear again (suggests copy-paste error)
    if len(stripped) > 500:
        head = stripped[:200].strip()
        if head and stripped.count(head) > 1:
            issues.append(QCIssue("WARN", "content",
                "First 200 chars appear multiple times — possible copy-paste duplication"))

    result.issues = issues
    if any(i.level == "CRITICAL" for i in issues):
        result.passed = False

    return result


def log_qc_result(result: QCResult, report_type: str) -> None:
    """Print a human-readable QC summary."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[qc {ts}] {report_type}: {result.summary()}", flush=True)
    for issue in result.issues:
        icon = "❌" if issue.level == "CRITICAL" else "⚠️"
        print(f"[qc {ts}]   {icon} [{issue.category}] {issue.detail}", flush=True)


# ── CLI for standalone use ──
if __name__ == "__main__":
    import argparse, sys
    parser = argparse.ArgumentParser(description="Preflight QC for outgoing reports")
    parser.add_argument("--stdin", action="store_true", help="Read body from stdin")
    parser.add_argument("--file", help="Read body from file")
    parser.add_argument("--type", default="generic", help="Report type label")
    parser.add_argument("--min-words", type=int, default=50, help="Minimum words (default: 50)")
    args = parser.parse_args()

    if args.stdin:
        body = sys.stdin.read()
    elif args.file:
        body = open(args.file).read()
    else:
        parser.print_help()
        sys.exit(1)

    result = check_report(body, report_type=args.type, min_words=args.min_words)
    log_qc_result(result, args.type)
    sys.exit(0 if result.passed else 1)
