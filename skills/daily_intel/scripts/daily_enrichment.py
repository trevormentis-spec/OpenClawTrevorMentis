#!/usr/bin/env python3
"""daily_enrichment.py — Before-assessment enrichment with real feed fetching.

Runs BEFORE generate_assessments.py to improve data quality:
  1. RSS feed fetching from major news/analysis sources
  2. Story freshness check (compare vs yesterday via story_tracker)
  3. Source freshness check (identify unused high-priority sources)
  4. Kalshi/Polymarket data integration
  5. Cross-source validation (narrative conflict detection)
  6. Produce enrichment report consumed by generate_assessments.py

Output: cron_tracking/enrichment_report.json
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import textwrap
import traceback
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, WORKSPACE, EXPORTS_DIR
from trevor_log import get_logger

log = get_logger("enrichment")

ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
STORY_DELTA = CRON_DIR / 'story_delta.json'
ENRICHMENT_FILE = CRON_DIR / 'enrichment_report.json'
STORY_TRACKER_FILE = CRON_DIR / 'story_tracker.json'
KALSHI_SCAN_DIR = WORKSPACE / 'exports'

# ── RSS Feed Registry ──
# Real RSS/Atom feeds that are actually fetched (not just listed)
RSS_FEEDS = {
    "bbc_world": {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "NEWS", "priority": 5},
    "bbc_middle_east": {"url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "category": "NEWS", "priority": 5},
    "reuters_world": {"url": "https://www.reutersagency.com/feed/", "category": "NEWS", "priority": 5},
    "ap_news": {"url": "https://apnews.com/rss/world", "category": "NEWS", "priority": 5},
    "al_jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "NEWS", "priority": 4},
    "the_diplomat": {"url": "https://thediplomat.com/feed/", "category": "NEWS", "priority": 3},
    "kyiv_post": {"url": "https://www.kyivpost.com/feed", "category": "NEWS", "priority": 3},
    "defense_news": {"url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "category": "NEWS", "priority": 3},
    "stratfor": {"url": "https://worldview.stratfor.com/rss", "category": "INTEL", "priority": 3},
}

# ── Theatre → keyword mappings for relevance filtering ──
THEATRE_KEYWORDS = {
    "europe": ["ukraine", "russia", "nato", "eu", "europe", "germany", "norway", "poland", "baltic"],
    "middle_east": ["iran", "hormuz", "israel", "gaza", "hezbollah", "yemen", "houthi", "iraq", "syria", "lebanon"],
    "asia": ["china", "taiwan", "india", "pakistan", "japan", "korea", "south china sea", "indo-pacific"],
    "north_america": ["mexico", "canada", "chihuahua", "cartel", "us mexico", "venezuela"],
    "south_america": ["cuba", "brazil", "venezuela", "colombia", "argentina", "latin america"],
    "africa": ["sahel", "mali", "niger", "burkina faso", "jnim", "nigeria", "ethiopia", "somalia"],
    "global_finance": ["oil", "brent", "wti", "opec", "sanctions", "energy", "inflation", "fed", "treasury"],
}

SOURCE_REGISTRY = {
    "NEWS": [
        {"name": "BBC News", "url": "https://www.bbc.com/news", "priority": 5},
        {"name": "Reuters", "url": "https://www.reuters.com", "priority": 5},
        {"name": "Associated Press", "url": "https://apnews.com", "priority": 5},
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com", "priority": 4},
        {"name": "The Diplomat", "url": "https://thediplomat.com", "priority": 3},
        {"name": "Kyiv Post", "url": "https://www.kyivpost.com", "priority": 3},
    ],
}


def fetch_rss_feed(feed_id: str, feed_info: dict) -> list[dict]:
    """Fetch and parse an RSS feed, returning article entries."""
    import urllib.request
    import xml.etree.ElementTree as ET
    
    entries = []
    try:
        req = urllib.request.Request(
            feed_info["url"],
            headers={"User-Agent": "TrevorIntelBot/1.0 (trevor@agentmail.to)"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
        
        root = ET.fromstring(xml_data)
        # Try standard RSS format first
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            entries.append({
                "feed": feed_id,
                "source": feed_info.get("url", ""),
                "title": title,
                "url": link,
                "summary": desc[:500] if desc else "",
                "published": pub_date,
            })
        
        # Try Atom format
        if not entries:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                link = link_el.get("href", "") if link_el is not None else ""
                summary = entry.findtext("{http://www.w3.org/2005/Atom}summary", "")
                updated = entry.findtext("{http://www.w3.org/2005/Atom}updated", "")
                entries.append({
                    "feed": feed_id,
                    "source": feed_info.get("url", ""),
                    "title": title,
                    "url": link,
                    "summary": summary[:500] if summary else "",
                    "published": updated,
                })
    except Exception as e:
        log.warning(f"Feed fetch failed: {feed_id}", error=str(e)[:100])
    
    return entries


def classify_to_theatre(article: dict) -> list[str]:
    """Classify an article to relevant theatres based on keyword matching."""
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    matches = []
    for theatre, keywords in THEATRE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matches.append(theatre)
                break
    return matches if matches else ["global"]


def fetch_all_feeds() -> list[dict]:
    """Fetch all RSS feeds and classify to theatres."""
    all_articles = []
    for feed_id, feed_info in RSS_FEEDS.items():
        articles = fetch_rss_feed(feed_id, feed_info)
        for article in articles:
            article["theatres"] = classify_to_theatre(article)
        all_articles.extend(articles)
        log.info(f"Feed {feed_id}: {len(articles)} articles")
    return all_articles


def cross_source_validate(articles: list[dict]) -> list[dict]:
    """Detect narrative conflicts across sources.
    Returns a list of conflict reports where sources disagree."""
    conflicts = []
    
    # Group articles by rough topic (using first 50 chars of title as key)
    topics = {}
    for article in articles:
        title = article.get("title", "")
        if not title:
            continue
        # Use first significant word pair as topic key
        words = title.split()[:3]
        key = " ".join(words).lower().strip(" ,.!?")
        if key not in topics:
            topics[key] = []
        topics[key].append(article)
    
    # Check for conflicting narratives within each topic group
    for topic, topic_articles in topics.items():
        if len(topic_articles) < 2:
            continue
        
        # Simple conflict detection: if two sources have very different framing
        # we flag it as potential conflict
        sources = set(a.get("feed", "") for a in topic_articles)
        if len(sources) >= 2:
            summaries = [a.get("summary", "")[:100] for a in topic_articles]
            # Check for contradictory language pairs
            conflict_pairs = [
                ("ceasefire", "strike"), ("deal", "collapse"), ("progress", "stall"),
                ("win", "lose"), ("agree", "reject"), ("accept", "refuse"),
            ]
            all_text = " ".join(summaries).lower()
            for pos, neg in conflict_pairs:
                if pos in all_text and neg in all_text:
                    conflicts.append({
                        "topic": topic,
                        "sources": list(sources),
                        "narrative": f"Sources disagree: '{pos}' vs '{neg}'",
                        "articles": [{"title": a.get("title"), "feed": a.get("feed")} for a in topic_articles[:3]],
                    })
                    break
    
    return conflicts


def check_source_freshness(articles: list[dict]) -> dict:
    """Check which high-priority sources are contributing vs missing."""
    used_sources = set()
    for article in articles:
        feed_id = article.get("feed", "")
        if feed_id in RSS_FEEDS:
            used_sources.add(RSS_FEEDS[feed_id]["url"])
    
    gaps = []
    for feed_id, feed_info in RSS_FEEDS.items():
        if feed_info["url"] not in used_sources and feed_info["priority"] >= 4:
            gaps.append({
                "feed": feed_id,
                "priority": feed_info["priority"],
                "category": feed_info["category"],
            })
    
    return {"used": len(used_sources), "total": len(RSS_FEEDS), "gaps": gaps}


def load_kalshi_data() -> list[dict]:
    """Load the latest Kalshi scan data."""
    today = datetime.date.today().strftime("%Y-%m-%d")
    kalshi_file = KALSHI_SCAN_DIR / f"kalshi-scan-{today}.md"
    
    if not kalshi_file.exists():
        # Try yesterday
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        kalshi_file = KALSHI_SCAN_DIR / f"kalshi-scan-{yesterday}.md"
    
    if not kalshi_file.exists():
        return []
    
    trades = []
    for line in kalshi_file.read_text().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 8 and parts[0].startswith("KX"):
            try:
                trades.append({
                    "ticker": parts[0],
                    "yes_bid": float(parts[1].replace("$", "")),
                    "volume": int(float(parts[6].replace(",", ""))),
                    "expiry": parts[7],
                })
            except (ValueError, IndexError):
                pass
    
    return sorted(trades, key=lambda x: x["volume"], reverse=True)[:10]


def main():
    """Run the full enrichment pipeline."""
    log.info("Starting enrichment")
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "articles_fetched": 0,
        "feeds_queried": 0,
        "sources_checked": {},
        "narrative_conflicts": [],
        "kalshi_trades": [],
        "story_freshness": {},
    }
    
    # 1. Fetch RSS feeds
    articles = fetch_all_feeds()
    report["articles_fetched"] = len(articles)
    report["feeds_queried"] = len(RSS_FEEDS)
    log.info(f"Fetched {len(articles)} articles from {len(RSS_FEEDS)} feeds")
    
    # 2. Cross-source validation
    conflicts = cross_source_validate(articles)
    report["narrative_conflicts"] = conflicts
    if conflicts:
        for c in conflicts[:5]:
            log.warning(f"Narrative conflict: {c['narrative']}", sources=c['sources'])
    
    # 3. Source freshness
    freshness = check_source_freshness(articles)
    report["sources_checked"] = freshness
    if freshness.get("gaps"):
        log.warning(f"Source gaps: {len(freshness['gaps'])} high-priority sources not reachable")
    
    # 4. Kalshi data
    kalshi = load_kalshi_data()
    report["kalshi_trades"] = kalshi
    log.info(f"Loaded {len(kalshi)} Kalshi trades")
    
    # 5. Story freshness from tracker
    if STORY_DELTA.exists():
        try:
            delta = json.loads(STORY_DELTA.read_text())
            report["story_freshness"] = delta
        except:
            pass
    
    # Save enrichment report
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    ENRICHMENT_FILE.write_text(json.dumps(report, indent=2))
    log.info(f"Enrichment report saved: {ENRICHMENT_FILE.name}")
    
    print(f"\n📡 Enrichment Summary:")
    print(f"  Feeds queried: {report['feeds_queried']}")
    print(f"  Articles fetched: {report['articles_fetched']}")
    print(f"  Narrative conflicts: {len(report['narrative_conflicts'])}")
    print(f"  Source gaps: {len(freshness.get('gaps', []))}")
    print(f"  Kalshi trades loaded: {len(report['kalshi_trades'])}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
