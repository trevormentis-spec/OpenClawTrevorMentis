#!/usr/bin/env python3
"""
GenViral Performance Aggregator

Takes the raw GenViral log (52+ posts), fixes the platform field,
groups by platform, date, hook_type, and produces aggregate stats.

Usage: python3 scripts/genviral_stats.py [--save]
"""

import json
import sys
from datetime import datetime
from collections import defaultdict

LOG_PATH = "skills/genviral/workspace/performance/log.json"

def load_log(path=LOG_PATH):
    with open(path) as f:
        data = json.load(f)
    return data.get("posts", [])

def guess_platform(account_id):
    """Map GenViral account IDs to platform names."""
    known = {
        "d3adbc5a-04fe-4dc1-93ab-b920f14ec968": "linkedin",
        "b03637b7-7043-4412-a408-6aac3da0ac25": "tiktok",
        # Add more as they appear
    }
    return known.get(account_id, "unknown")

def aggregate(posts):
    # Fix platform field from account_id
    for p in posts:
        if p.get("platform") in ("unknown", None):
            p["platform"] = guess_platform(p.get("account_id", ""))

    by_platform = defaultdict(lambda: {
        "count": 0, "total_views": 0, "total_likes": 0,
        "total_comments": 0, "total_shares": 0, "with_engagement": 0
    })
    by_date = defaultdict(lambda: {
        "count": 0, "total_views": 0, "total_likes": 0,
        "total_comments": 0, "total_shares": 0, "platforms": set()
    })
    by_hook = defaultdict(lambda: {
        "count": 0, "total_views": 0, "total_likes": 0
    })
    total_views = 0
    total_likes = 0

    for p in posts:
        plat = p.get("platform", "unknown")
        date = p.get("date", "unknown")
        hook_type = p.get("hook_type", "unknown")
        m = p.get("metrics", {})
        v = m.get("views", 0)
        l = m.get("likes", 0)
        c = m.get("comments", 0)
        s = m.get("shares", 0)

        by_platform[plat]["count"] += 1
        by_platform[plat]["total_views"] += v
        by_platform[plat]["total_likes"] += l
        by_platform[plat]["total_comments"] += c
        by_platform[plat]["total_shares"] += s
        if v > 0 or l > 0:
            by_platform[plat]["with_engagement"] += 1

        by_date[date]["count"] += 1
        by_date[date]["total_views"] += v
        by_date[date]["total_likes"] += l
        by_date[date]["total_comments"] += c
        by_date[date]["total_shares"] += s
        by_date[date]["platforms"].add(plat)

        by_hook[hook_type]["count"] += 1
        by_hook[hook_type]["total_views"] += v
        by_hook[hook_type]["total_likes"] += l

        total_views += v
        total_likes += l

    return by_platform, by_date, by_hook, total_views, total_likes

def render_report(by_platform, by_date, by_hook, total_views, total_likes, posts):
    lines = []
    lines.append("# GenViral Performance Report")
    lines.append(f"\n**Total posts:** {len(posts)}")
    lines.append(f"**Total views:** {total_views}")
    lines.append(f"**Total likes:** {total_likes}")
    lines.append(f"\n**Date range:** {min(p.get('date','') for p in posts)} — {max(p.get('date','') for p in posts)}")

    lines.append("\n## By Platform\n")
    lines.append("| Platform | Posts | Views | Likes | Comments | Shares | Engaged Posts |")
    lines.append("|----------|-------|-------|-------|----------|--------|---------------|")
    for plat, stats in sorted(by_platform.items()):
        lines.append(
            f"| {plat} | {stats['count']} | {stats['total_views']} | "
            f"{stats['total_likes']} | {stats['total_comments']} | "
            f"{stats['total_shares']} | {stats['with_engagement']} |"
        )

    lines.append("\n## By Date\n")
    lines.append("| Date | Posts | Views | Likes | Comments | Shares | Platforms |")
    lines.append("|------|-------|-------|-------|----------|--------|-----------|")
    for date in sorted(by_date.keys()):
        stats = by_date[date]
        platforms = ", ".join(sorted(stats["platforms"]))
        lines.append(
            f"| {date} | {stats['count']} | {stats['total_views']} | "
            f"{stats['total_likes']} | {stats['total_comments']} | "
            f"{stats['total_shares']} | {platforms} |"
        )

    lines.append("\n## By Hook Type\n")
    lines.append("| Hook Type | Posts | Views | Likes |")
    lines.append("|-----------|-------|-------|-------|")
    for hook, stats in sorted(by_hook.items()):
        lines.append(f"| {hook} | {stats['count']} | {stats['total_views']} | {stats['total_likes']} |")

    lines.append("\n## Orphaned (No Platform)\n")
    orphaned = [p for p in posts if p.get("platform") in ("unknown", None)]
    for p in orphaned:
        lines.append(f"- {p.get('id','?')}: account_id={p.get('account_id','?')} date={p.get('date','?')}")

    return "\n".join(lines)

def main():
    posts = load_log()
    if not posts:
        print("No posts found in log.")
        return

    by_platform, by_date, by_hook, total_views, total_likes = aggregate(posts)
    report = render_report(by_platform, by_date, by_hook, total_views, total_likes, posts)

    if "--save" in sys.argv:
        outpath = "exports/social/genviral-stats-2026-05-13.md"
        with open(outpath, "w") as f:
            f.write(report)
        print(f"Report saved to {outpath}")
    else:
        print(report)

if __name__ == "__main__":
    main()
