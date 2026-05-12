#!/usr/bin/env python3
"""
scrape_creators.py — Social media intelligence collection via ScrapeCreators API.

Provides real-time OSINT from 30+ social media platforms for Trevor's
collection pipeline. Used for:
- Influencer/viral content monitoring per region
- Narrative tracking on TikTok, Instagram, X, Reddit, Telegram
- Early warning signal detection from social media chatter
- Geopolitical sentiment analysis per theatre

Usage:
    from scrape_creators import ScrapeCreators
    sc = ScrapeCreators()
    profile = sc.profile("worldeconomicforum", "tiktok")
    posts = sc.posts("worldeconomicforum", "tiktok", count=5)
    trending = sc.trending_hashtags("tiktok", "us")
"""
from __future__ import annotations

import datetime
import json
import os
import time
import urllib.request
import urllib.parse

BASE_URL = "https://api.scrapecreators.com/v1"
API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "mYa56PnRKges2xHchvb4Jx7YND43")

# Platform taxonomy for intelligence relevance
PLATFORM_INTEL_VALUE = {
    "telegram": 9,    # High intel value — organizational communication
    "tiktok": 7,      # Rising — narrative formation, youth mobilization
    "x": 8,           # High — real-time elite discourse
    "reddit": 6,      # Medium — community sentiment
    "instagram": 5,   # Medium — visual narrative tracking
    "youtube": 6,     # Medium — long-form discourse
    "facebook": 4,    # Low-medium — broad demographic
    "threads": 3,     # Low — nascent platform
    "bluesky": 4,     # Low-medium — academic/journalist heavy
    "linkedin": 3,    # Low — professional network
}


class ScrapeCreators:
    """Client for ScrapeCreators social media intelligence API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or API_KEY
        self.base_url = BASE_URL
        self.credits_remaining = 0

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}/{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"x-api-key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                if isinstance(data, dict):
                    self.credits_remaining = data.get("credits_remaining", self.credits_remaining)
                return data
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")[:200]
            return {"error": f"HTTP {e.code}: {err}"}
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, body: dict) -> dict:
        """Make a POST request to the API."""
        url = f"{self.base_url}/{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data,
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")[:200]
            return {"error": f"HTTP {e.code}: {err}"}

    def credits(self) -> int:
        """Check remaining credits."""
        result = self._get("account/credit-balance")
        self.credits_remaining = result.get("creditCount", 0)
        return self.credits_remaining

    def profile(self, handle: str, platform: str = "tiktok") -> dict:
        """Get profile information for a social media account."""
        return self._get(f"{platform}/profile", {"handle": handle})

    def posts(self, handle: str, platform: str = "tiktok", count: int = 5) -> list[dict]:
        """Get recent posts from an account."""
        result = self._get(f"{platform}/posts", {"handle": handle, "count": count})
        return result.get("posts", result.get("videos", []))

    def search(self, query: str, platform: str = "tiktok", count: int = 5) -> list[dict]:
        """Search for content across a platform."""
        result = self._get(f"{platform}/search", {"query": query, "count": count})
        return result.get("results", result.get("videos", []))

    def trending_tags(self, platform: str = "tiktok", region: str = "us") -> list[dict]:
        """Get trending hashtags for a platform and region."""
        result = self._get(f"{platform}/trending", {"region": region})
        return result.get("trending", [])

    def monitor_theatre(self, theatre_key: str, keywords: list[str],
                        platforms: list[str] | None = None) -> dict:
        """Monitor a geopolitical theatre for social media signals.
        
        Returns structured intelligence: trending narratives, viral content,
        influential accounts, and sentiment indicators per platform.
        """
        if platforms is None:
            platforms = ["tiktok", "x", "telegram", "reddit"]

        results = {}
        for platform in platforms:
            if self.credits_remaining < 5:
                break
            platform_results = []
            for keyword in keywords[:3]:  # limit to 3 keywords per theatre
                posts_data = self.search(keyword, platform, count=3)
                if posts_data and isinstance(posts_data, list):
                    platform_results.extend(posts_data)
                time.sleep(0.3)  # rate limit courtesy
            if platform_results:
                results[platform] = {
                    "total_posts_found": len(platform_results),
                    "sample_posts": [
                        {
                            "text": p.get("text", p.get("description", ""))[:200],
                            "engagement": p.get("likes", p.get("plays", 0)),
                            "author": p.get("author", p.get("authorMeta", {}).get("name", "?")),
                            "url": p.get("url", p.get("webVideoUrl", "")),
                            "timestamp": p.get("createTime", p.get("created_at", "")),
                        }
                        for p in platform_results[:5]
                    ],
                }
        return results


# ── Factory for pipeline integration ──
def get_scraper() -> ScrapeCreators:
    """Get a configured ScrapeCreators client."""
    return ScrapeCreators()
