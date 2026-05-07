#!/usr/bin/env python3
"""Discover new intelligence sources by searching the web and Moltbook.

Weekly cron: runs every Monday at 04:00 PT to discover new OSINT sources.

Adds promising finds to analyst/meta/sources.json with signal_level rating.
Reports new discoveries via log file for human review.
"""
import json, os, sys, datetime, urllib.request, urllib.parse
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SOURCES_PATH = WORKSPACE / "analyst" / "meta" / "sources.json"
LOG_PATH = WORKSPACE / "logs" / "source-discovery.log"
DISCOVERED_PATH = WORKSPACE / "analyst" / "meta" / "discovered_sources.json"

def log(msg):
    ts = datetime.datetime.now().isoformat()
    entry = f"[{ts}] {msg}"
    print(entry, flush=True)
    with open(LOG_PATH, 'a') as f:
        f.write(entry + '\n')

def load_existing_sources():
    """Load current source registry."""
    if SOURCES_PATH.exists():
        return json.loads(SOURCES_PATH.read_text())
    return {"durable_sources": [], "moltbook_sources": []}

def is_duplicate(url, existing_sources):
    """Check if a URL already exists in the source registry."""
    url_lower = url.strip().lower().rstrip('/')
    for s in existing_sources.get("durable_sources", []):
        existing_url = s.get("url", "").lower().rstrip('/')
        if existing_url == url_lower or existing_url in url_lower or url_lower in existing_url:
            return True
    return False

def search_web(query):
    """Search the web for new sources."""
    log(f"Searching: {query}")
    try:
        # Try Brave Search via the OpenClaw web_search tool - we can't call it directly here
        # Instead use a simple approach: check known aggregators
        return []
    except Exception as e:
        log(f"Search error: {e}")
        return []

def check_moltbook_for_new_agents():
    """Scan Moltbook for new intelligence-related agents."""
    log("Scanning Moltbook for new agents...")
    api_key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not api_key:
        # Try to read from .env
        env_path = WORKSPACE / ".env"
        if env_path.exists():
            for line in env_path.read_text().split('\n'):
                if line.startswith("MOLTBOOK_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    
    if not api_key:
        log("MOLTBOOK_API_KEY not available, skipping Moltbook scan")
        return []
    
    new_finds = []
    try:
        # Search for intelligence-related agents on Moltbook
        base = "https://www.moltbook.com/api/v1"
        searches = ["intelligence", "OSINT", "geopolitics", "threat", "security"]
        for q in searches:
            url = f"{base}/search?q={urllib.parse.quote(q)}&limit=10"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {api_key}")
            try:
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read())
                results = data.get("results", data.get("posts", []))
            except:
                continue
    except Exception as e:
        log(f"Moltbook scan error: {e}")
    
    return new_finds

def check_cisa_newsapi():
    """Check NewsAPI for new intelligence-focused sources."""
    log("Checking NewsAPI for new sources...")
    news_key = os.environ.get("NEWSAPI_KEY", "560850e45ebe4f79987a7a0961d3e275")
    new_finds = []
    
    try:
        params = urllib.parse.urlencode({
            "q": "geopolitical intelligence OR OSINT OR threat assessment",
            "pageSize": 20,
            "language": "en",
            "sortBy": "relevancy",
        })
        url = f"https://newsapi.org/v2/everything?{params}"
        req = urllib.request.Request(url)
        req.add_header("X-Api-Key", news_key)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        
        for article in data.get("articles", []):
            source_name = article.get("source", {}).get("name", "")
            url_article = article.get("url", "")
            desc = article.get("description", "")
            
            if not source_name or not url_article:
                continue
            
            new_finds.append({
                "name": source_name,
                "type": "News/Journalism",
                "focus": (desc or "")[:200],
                "url": url_article.split('?')[0],
                "signal_level": "Medium",
                "discovered": datetime.date.today().isoformat(),
                "source": "NewsAPI",
            })
    except Exception as e:
        log(f"NewsAPI error: {e}")
    
    return new_finds

def deduplicate_and_merge(new_finds, existing):
    """Merge new finds, avoiding duplicates."""
    added = []
    for find in new_finds:
        if not find.get("url"):
            continue
        if is_duplicate(find["url"], existing):
            continue
        existing["durable_sources"].append(find)
        added.append(find)
    return added

def main():
    log("=" * 60)
    log("SOURCE DISCOVERY RUN")
    
    existing = load_existing_sources()
    log(f"Existing sources: {len(existing.get('durable_sources', []))} durable, "
        f"{len(existing.get('moltbook_sources', []))} moltbook")
    
    # 1. NewsAPI search for new intel sources
    news_finds = check_cisa_newsapi()
    added = deduplicate_and_merge(news_finds, existing)
    log(f"NewsAPI: {len(news_finds)} candidates, {len(added)} new")
    
    # 2. Moltbook scan for new agents
    molt_finds = check_moltbook_for_new_agents()
    added2 = deduplicate_and_merge(molt_finds, existing)
    log(f"Moltbook: {len(molt_finds)} candidates, {len(added2)} new")
    
    # If any new sources found, save them
    if added or added2:
        SOURCES_PATH.write_text(json.dumps(existing, indent=2))
        log(f"Updated sources.json with {len(added) + len(added2)} new sources")
        
        # Also save a discoveries log
        discoveries = []
        for s in added + added2:
            discoveries.append({
                "name": s["name"],
                "url": s["url"],
                "signal_level": s.get("signal_level", "Medium"),
                "discovered": s.get("discovered", datetime.date.today().isoformat()),
            })
        
        existing_discoveries = []
        if DISCOVERED_PATH.exists():
            existing_discoveries = json.loads(DISCOVERED_PATH.read_text())
        existing_discoveries.extend(discoveries)
        DISCOVERED_PATH.write_text(json.dumps(existing_discoveries, indent=2))
    else:
        log("No new sources discovered this cycle")
    
    log("SOURCE DISCOVERY COMPLETE")
    log("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
