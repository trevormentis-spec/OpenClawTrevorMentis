#!/usr/bin/env python3
"""QC Resolution Workflow — CLI for recording brief/deliverable reviews.

Records human analyst review decisions:
- approved: Brief passes QC, ready for delivery
- rejected: Brief fails QC, must be regenerated
- revision_needed: Brief needs targeted edits before delivery

All decisions append to memory/qc-reviews.jsonl with full audit trail.

Usage:
    python3 scripts/qc_resolve.py --brief path/to/brief.md --status approved
    python3 scripts/qc_resolve.py --brief path/to/brief.md --status rejected --reason "Fabrication in Section 3"
    python3 scripts/qc_resolve.py --brief path/to/brief.md --status revision_needed --reason "Missing Kalshi data"
    python3 scripts/qc_resolve.py --list                    # Show all reviews
    python3 scripts/qc_resolve.py --list --pending          # Show pending items
    python3 scripts/qc_resolve.py --stats                   # Review statistics
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
QC_REVIEWS_PATH = REPO_ROOT / "memory" / "qc-reviews.jsonl"
COLLECTION_DB = REPO_ROOT / "data" / "collection_records.db"

VALID_STATUSES = ("approved", "rejected", "revision_needed")


def log(msg: str) -> None:
    print(f"[qc-resolve] {msg}", file=sys.stderr, flush=True)


def _file_hash(path: pathlib.Path) -> str:
    """SHA256 hash of file contents."""
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def read_reviews() -> list[dict]:
    """Read all QC reviews from JSONL."""
    if not QC_REVIEWS_PATH.exists():
        return []
    reviews = []
    for line in QC_REVIEWS_PATH.read_text().strip().split("\n"):
        line = line.strip()
        if line:
            try:
                reviews.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return reviews


def record_review(
    brief_path: str,
    status: str,
    reason: str = "",
    reviewer: str = "human_analyst",
    tags: list[str] | None = None,
) -> dict:
    """Record a QC review decision.

    Args:
        brief_path: Path to the brief being reviewed
        status: One of approved, rejected, revision_needed
        reason: Free-text explanation
        reviewer: Who performed the review
        tags: Optional category tags

    Returns:
        The review record dict
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

    brief = pathlib.Path(brief_path)
    now = dt.datetime.now(dt.timezone.utc)

    review = {
        "review_id": f"qc-{now.strftime('%Y%m%d%H%M%S')}-{_file_hash(brief)[:8]}",
        "brief_path": str(brief.relative_to(REPO_ROOT)) if brief.is_relative_to(REPO_ROOT) else str(brief),
        "brief_hash": _file_hash(brief),
        "status": status,
        "reason": reason,
        "reviewer": reviewer,
        "tags": tags or [],
        "reviewed_at": now.isoformat(),
        "brief_exists": brief.exists(),
    }

    # If brief has a corresponding JSON, check for generation metadata
    json_path = brief.with_suffix(".json")
    if json_path.exists():
        try:
            brief_data = json.loads(json_path.read_text())
            review["directive"] = brief_data.get("directive", "")
            review["total_words"] = brief_data.get("total_words", 0)
            review["sections_count"] = len(brief_data.get("sections", []))
        except (json.JSONDecodeError, OSError):
            pass

    # Append to JSONL
    QC_REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QC_REVIEWS_PATH, "a") as f:
        f.write(json.dumps(review, ensure_ascii=False) + "\n")

    log(f"Review recorded: {review['review_id']} — {status}")
    return review


def update_collection_qc(brief_path: str, new_status: str) -> int:
    """Update QC status in collection_records.db for records matching this brief.

    Returns count of updated records.
    """
    if not COLLECTION_DB.exists():
        return 0

    import sqlite3
    brief_name = pathlib.Path(brief_path).stem

    # Map review status to collection QC status
    qc_map = {
        "approved": "APPROVED",
        "rejected": "REJECTED",
        "revision_needed": "REVISION_NEEDED",
    }
    new_qc = qc_map.get(new_status, "PENDING_HUMAN_ANALYST_QC_REVIEW")

    conn = sqlite3.connect(str(COLLECTION_DB))
    cursor = conn.execute(
        "UPDATE collection_records SET qc_status = ? WHERE source LIKE ? AND qc_status = 'PENDING_HUMAN_ANALYST_QC_REVIEW'",
        (new_qc, f"%{brief_name}%"),
    )
    updated = cursor.rowcount
    conn.commit()
    conn.close()

    if updated > 0:
        log(f"Updated {updated} collection record(s) to {new_qc}")
    return updated


def list_reviews(pending_only: bool = False) -> list[dict]:
    """List all reviews, optionally filtered to pending."""
    reviews = read_reviews()
    if pending_only:
        # Find briefs that haven't been approved
        approved_paths = {r["brief_path"] for r in reviews if r["status"] == "approved"}
        # Get unique brief paths
        all_paths = {r["brief_path"] for r in reviews}
        pending_paths = all_paths - approved_paths
        reviews = [r for r in reviews if r["brief_path"] in pending_paths]
    return reviews


def review_stats() -> dict:
    """Generate review statistics."""
    reviews = read_reviews()
    if not reviews:
        return {"total": 0, "by_status": {}, "by_reviewer": {}, "approval_rate": 0.0, "recent": []}

    by_status = {}
    by_reviewer = {}
    for r in reviews:
        status = r.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        reviewer = r.get("reviewer", "unknown")
        by_reviewer[reviewer] = by_reviewer.get(reviewer, 0) + 1

    # Approval rate
    total = len(reviews)
    approved = by_status.get("approved", 0)
    approval_rate = round(approved / max(total, 1), 3)

    # Recent reviews (last 10)
    recent = sorted(reviews, key=lambda r: r.get("reviewed_at", ""), reverse=True)[:10]

    return {
        "total": total,
        "by_status": by_status,
        "by_reviewer": by_reviewer,
        "approval_rate": approval_rate,
        "recent": [
            {
                "review_id": r.get("review_id", "?"),
                "brief": r.get("brief_path", "?"),
                "status": r.get("status", "?"),
                "reviewed_at": r.get("reviewed_at", "?")[:16],
            }
            for r in recent
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="QC Resolution Workflow")
    parser.add_argument("--brief", help="Path to brief file to review")
    parser.add_argument("--status", choices=VALID_STATUSES, help="Review decision")
    parser.add_argument("--reason", default="", help="Reason for decision")
    parser.add_argument("--reviewer", default="human_analyst", help="Reviewer identifier")
    parser.add_argument("--tags", nargs="*", default=[], help="Category tags")
    parser.add_argument("--list", action="store_true", dest="list_reviews", help="List all reviews")
    parser.add_argument("--pending", action="store_true", help="Filter to pending reviews")
    parser.add_argument("--stats", action="store_true", help="Show review statistics")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.stats:
        stats = review_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"QC Review Statistics")
            print(f"  Total reviews: {stats['total']}")
            print(f"  Approval rate: {stats['approval_rate']:.0%}")
            for status, count in stats.get("by_status", {}).items():
                print(f"  {status}: {count}")
            if stats["recent"]:
                print(f"\n  Recent reviews:")
                for r in stats["recent"][:5]:
                    print(f"    [{r['status']:17s}] {r['brief']} ({r['reviewed_at']})")
        return 0

    if args.list_reviews:
        reviews = list_reviews(pending_only=args.pending)
        if args.json:
            print(json.dumps(reviews, indent=2))
        else:
            label = "Pending" if args.pending else "All"
            print(f"{label} QC Reviews ({len(reviews)} total):")
            for r in reviews:
                print(f"  [{r.get('status', '?'):17s}] {r.get('brief_path', '?')} — {r.get('reason', 'no reason')[:50]}")
        return 0

    if not args.brief or not args.status:
        parser.print_help()
        return 1

    if not pathlib.Path(args.brief).exists():
        log(f"Warning: brief file not found: {args.brief} (recording review anyway)")

    review = record_review(
        args.brief,
        args.status,
        reason=args.reason,
        reviewer=args.reviewer,
        tags=args.tags,
    )

    # Also update collection records QC status
    updated = update_collection_qc(args.brief, args.status)

    if args.json:
        review["collection_records_updated"] = updated
        print(json.dumps(review, indent=2))
    else:
        print(f"Review recorded: {review['review_id']}")
        print(f"  Brief: {review['brief_path']}")
        print(f"  Status: {review['status']}")
        if review.get("reason"):
            print(f"  Reason: {review['reason']}")
        if updated > 0:
            print(f"  Collection records updated: {updated}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
