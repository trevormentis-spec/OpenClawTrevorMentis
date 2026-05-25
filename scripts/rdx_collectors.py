#!/usr/bin/env python3
"""
RDX and C4 Supply Market Data Collectors — multi-layer feed monitoring.

Wires in GDELT news monitoring, Telegram OSINT channel scraping,
USAspending contract tracking, corporate filings monitoring,
and trade data snapshot collection.

Usage:
    python3 scripts/rdx_collectors.py --gdelt-daily       # GDELT news sweep
    python3 scripts/rdx_collectors.py --osint-daily        # Telegram OSINT channels
    python3 scripts/rdx_collectors.py --contracts-weekly   # USAspending contracts
    python3 scripts/rdx_collectors.py --filings-weekly     # Corporate filings
    python3 scripts/rdx_collectors.py --all-daily          # All daily tasks
    python3 scripts/rdx_collectors.py --compile            # Compile tracker
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RDX_DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "rdx_c4_supply"
RDX_FEEDS_DIR = RDX_DATA_DIR / "data_feeds"
RDX_CONTRACTS_DIR = RDX_DATA_DIR / "contracts"
RDX_OSINT_DIR = RDX_DATA_DIR / "osint_feeds"
STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "rdx-collector-state.json"

# Producer names for entity matching
PRODUCERS = [
    "Holston", "BAE Systems", "Radford", "Eurenco", "Nitro-Chem",
    "Chemring Nobel", "Rheinmetall", "Varpalota", "Hanwha",
    "Solar Industries", "Premier Explosives", "Poongsan",
    "Sverdlov", "Bryansk Chemical", "Promsintez", "Metafrax",
    "Norinco", "Explosia", "Nammo", "Orica", "Dyno Nobel",
]

# GDELT keywords for RDX/C4 monitoring
GDELT_KEYWORDS = [
    "RDX", "hexogen", "cyclonite", "C-4", "C4 explosive", "HMX", "octogen",
    "Composition B", "PBXN", "IMX-101", "CL-20", "nitrocellulose",
    "hexamine", "urotropine", "Holston", "Eurenco", "Bergerac",
    "Nitro-Chem", "Bydgoszcz", "Chemring Nobel", "Varpalota",
    "Sverdlov plant", "Promsintez", "Bryansk Chemical",
    "Dorogobuzh", "Metafrax", "explosives plant",
]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[rdx-collect {ts}] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_gdelt": None, "last_osint": None, "last_contracts": None,
            "seen_articles": [], "seen_events": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def save_output(name: str, data: dict) -> None:
    RDX_FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    date_slug = dt.date.today().isoformat()
    path = RDX_FEEDS_DIR / f"{name}-{date_slug}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    log(f"Saved: {path}")


# =========================================================================
# COLLECTOR 1: GDELT News Sweep (Daily)
# =========================================================================

def collect_gdelt_daily() -> dict:
    """Query GDELT 2.0 GKG for recent RDX/C4-related news."""
    log("Running GDELT sweep for RDX/C4 keywords...")
    state = load_state()
    seen = set(state.get("seen_articles", []))

    results = []
    for keyword in GDELT_KEYWORDS[:10]:  # First 10 keywords per run to spread load
        encoded = urllib.parse.quote(f'"{keyword}" explosives military')
        # Use Google News search as a GDELT proxy
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        try:
            import feedparser
            feed = feedparser.parse(url)
            for entry in feed.get("entries", [])[:5]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                source = entry.get("source", {}).get("title", "") if hasattr(entry.get("source", {}), "get") else ""
                
                sig = f"{title[:80]}|{link[:80]}"
                if sig in seen:
                    continue
                seen.add(sig)
                
                results.append({
                    "keyword": keyword,
                    "title": title,
                    "url": link,
                    "published": published,
                    "source": source,
                    "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                })
        except Exception as e:
            log(f"  GDELT query failed for '{keyword}': {e}")
            continue

    # Update state
    state["seen_articles"] = list(seen)[-500:]  # Keep last 500
    state["last_gdelt"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_state(state)

    # Log to episodic memory
    if results:
        log_to_episodic({
            "type": "rdx_gdelt_sweep",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "articles_found": len(results),
            "keywords_used": GDELT_KEYWORDS[:10],
            "top_articles": [{"title": r["title"][:80], "keyword": r["keyword"]} for r in results[:10]],
        })

    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "articles_found": len(results),
        "articles": results[:50],
    }
    save_output("gdelt-sweep", output)
    return output


# =========================================================================
# COLLECTOR 2: Telegram OSINT Channels (Daily)
# =========================================================================

def collect_osint_daily() -> dict:
    """Check Telegram OSINT channels for Russian explosives plant reports.
    Uses t.me web previews and public RSS bridges."""
    log("Checking OSINT channels for Russian explosives plant activity...")
    
    channels = [
        {"name": "CyberBoroshno", "url": "https://t.me/s/cyberboroshno"},
        {"name": "Dnipro OSINT", "url": "https://t.me/s/dnipro_osint"},
        {"name": "Exilenova+", "url": "https://t.me/s/exilenova_plus"},
        {"name": "Militarnyi", "url": "https://militarnyi.com/en/"},
        {"name": "Defence-Blog", "url": "https://www.defence-blog.com/"},
    ]
    
    state = load_state()
    seen = set(state.get("seen_events", []))
    events = []
    
    for channel in channels:
        try:
            req = urllib.request.Request(
                channel["url"],
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            
            # Look for Russian plant names and date patterns
            for producer in PRODUCERS:
                if producer.lower() in html.lower():
                    # Check if it mentions strike, damage, explosion
                    context_matches = re.findall(
                        rf".{{0,100}}{re.escape(producer)}.{{0,100}}",
                        html,
                        re.IGNORECASE,
                    )
                    for ctx in context_matches[:3]:
                        if any(kw in ctx.lower() for kw in ["strike", "damage", "explos", "hit", "drone", "fire", "blast"]):
                            sig = f"{channel['name']}|{producer}|{ctx[:60]}"
                            if sig not in seen:
                                seen.add(sig)
                                events.append({
                                    "channel": channel["name"],
                                    "producer": producer,
                                    "context": ctx.strip()[:200],
                                    "detected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                                })
        except Exception as e:
            log(f"  Channel {channel['name']} failed: {e}")
    
    state["seen_events"] = list(seen)[-300:]
    state["last_osint"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_state(state)
    
    # Log to episodic
    if events:
        log_to_episodic({
            "type": "rdx_osint_check",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "events_found": len(events),
            "events": [{"channel": e["channel"], "producer": e["producer"]} for e in events],
        })
    
    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "channels_checked": len(channels),
        "events_found": len(events),
        "events": events[:30],
    }
    save_output("osint-events", output)
    return output


# =========================================================================
# COLLECTOR 3: Government Contracts (Weekly)
# =========================================================================

def collect_contracts_weekly() -> dict:
    """Check USAspending.gov for recent RDX/HMX/explosives contracts."""
    log("Checking USAspending for explosives contracts...")
    
    contracts = []
    
    # Search USAspending API for explosives contracts
    # NAICS 325920 = Explosives Manufacturing
    # NAICS 332993 = Ammunition Manufacturing
    for naics in ["325920", "332993"]:
        try:
            url = f"https://api.usaspending.gov/api/v2/search/spending_by_category/ awarding_agency/?filters={{'naics_codes':['{naics}'],'time_period':[{{'start_date':'2026-01-01','end_date':'2026-12-31'}}]}}"
            # Simpler: search by keyword
            url = f"https://api.usaspending.gov/api/v2/search/spending_by_transaction/?filters={{'keywords':['RDX','HMX','explosives','propellant'],'time_period':[{{'start_date':'2026-01-01','end_date':'2026-12-31'}}]}}&limit=20"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TrevorIntel/1.0", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
                for r in data.get("results", []):
                    contracts.append({
                        "award_id": r.get("generated_unique_award_id", ""),
                        "recipient": r.get("recipient_name", ""),
                        "amount": r.get("federal_action_obligation", 0),
                        "description": (r.get("description", "") or "")[:200],
                        "date": r.get("period_of_performance_current_end_date", ""),
                        "agency": r.get("awarding_agency_name", ""),
                    })
        except Exception as e:
            log(f"  USAspending query failed: {e}")
    
    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "contracts_found": len(contracts),
        "contracts": contracts[:30],
        "total_value": sum(c.get("amount", 0) or 0 for c in contracts),
    }
    save_output("contracts", output)
    return output


# =========================================================================
# COLLECTOR 4: Corporate Filings (Weekly)
# =========================================================================

def collect_filings_weekly() -> dict:
    """Check for recent corporate announcements from key public companies."""
    log("Checking corporate filings for RDX-related announcements...")
    
    companies = [
        {"name": "BAE Systems", "ticker": "BAES", "exchange": "LSE"},
        {"name": "Rheinmetall", "ticker": "RHM", "exchange": "XETRA"},
        {"name": "Chemring Group", "ticker": "CHG", "exchange": "LSE"},
        {"name": "Hanwha Corporation", "ticker": "000880", "exchange": "KRX"},
        {"name": "Orica Limited", "ticker": "ORI", "exchange": "ASX"},
        {"name": "Solar Industries", "ticker": "SOLARINDS", "exchange": "NSE"},
    ]
    
    # Search for news about these companies related to RDX/explosives
    news_items = []
    for company in companies:
        query = urllib.parse.quote(f"{company['name']} RDX explosives contract")
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            import feedparser
            feed = feedparser.parse(url)
            for entry in feed.get("entries", [])[:3]:
                news_items.append({
                    "company": company["name"],
                    "ticker": company["ticker"],
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": entry.get("source", {}).get("title", "") if hasattr(entry.get("source", {}), "get") else "",
                })
        except Exception as e:
            log(f"  {company['name']} query failed: {e}")
    
    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "companies_checked": len(companies),
        "news_items": len(news_items),
        "items": news_items[:30],
    }
    save_output("corporate-filings", output)
    return output


# =========================================================================
# COLLECTOR 5: Weekly tracking brief compilation
# =========================================================================

def compile_tracker() -> dict:
    """Compile all collected data into a market tracker snapshot."""
    log("Compiling RDX/C4 market tracker...")
    
    tracker = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "data_feeds": {},
    }
    
    for prefix in ["gdelt-sweep", "osint-events", "contracts", "corporate-filings"]:
        files = sorted(RDX_FEEDS_DIR.glob(f"{prefix}-*.json"), reverse=True)
        if files:
            try:
                tracker["data_feeds"][prefix] = json.loads(files[0].read_text())
            except Exception:
                tracker["data_feeds"][prefix] = {"status": "unreadable"}

    # Count Russian plant events from OSINT
    osint_events = tracker.get("data_feeds", {}).get("osint-events", {}).get("events", [])
    russian_plants = {}
    for ev in osint_events:
        name = ev.get("producer", "")
        russian_plants[name] = russian_plants.get(name, 0) + 1
    
    tracker["russian_plant_alerts"] = len(osint_events)
    tracker["russian_plant_counts"] = russian_plants
    
    date_slug = dt.date.today().isoformat()
    path = RDX_FEEDS_DIR / f"market-tracker-{date_slug}.json"
    path.write_text(json.dumps(tracker, indent=2, default=str))
    log(f"Market tracker saved: {path}")
    return tracker


def log_to_episodic(record: dict) -> None:
    """Write a record to episodic memory."""
    ep_dir = REPO_ROOT / "brain" / "memory" / "episodic"
    ep_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    with open(ep_dir / f"{today}.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")


# =========================================================================
# Main
# =========================================================================


# =========================================================================
# CREATIVE SOURCE COLLECTORS
# =========================================================================

def collect_epa_tri() -> dict:
    """EPA Toxics Release Inventory — production change signals from explosives plants."""
    log("Checking EPA TRI for explosives plant signals...")
    results = []
    for fac in [{"name": "Holston AAP", "city": "Kingsport", "state": "TN"}, {"name": "Radford AAP", "city": "Radford", "state": "VA"}]:
        try:
            q = urllib.parse.quote(f"{fac['name']} {fac['city']} {fac['state']}")
            url = f"https://data.epa.gov/efservice/PUBLIC_CONTACT/FACILITY_NAME/{q}/json"
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorIntel/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                results.append({"facility": fac['name'], "status": "found", "records": len(data) if isinstance(data, list) else 1})
        except Exception as e:
            results.append({"facility": fac['name'], "status": "unavailable", "note": str(e)[:80]})
    out = {"status": "ok", "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "facilities": results}
    save_output("epa-tri", out)
    return out

def _brave_search(query: str, count: int = 5) -> list:
    """Search via Brave Search API."""
    key = os.environ.get("BRAVE_API_KEY", "")
    if not key:
        env_file = REPO_ROOT.parent / ".env" if 'REPO_ROOT' in dir() else pathlib.Path(__file__).resolve().parent.parent / ".env"
        # From env
        try:
            for line in open(REPO_ROOT / ".env").read().split("\n"):
                if "BRAVE_API_KEY=" in line:
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    break
        except:
            pass
    if not key:
        return []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={count}"
        req = urllib.request.Request(url, headers={"Accept": "application/json", "X-Subscription-Token": key})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            data = json.loads(raw)
        return data.get("web", {}).get("results", [])
    except Exception as e:
        log(f"  Brave search failed: {e}")
        return []

def collect_jobs() -> dict:
    """Job posting signals — hiring at explosives plants = expansion."""
    log("Scanning job postings for explosives hiring...")
    signals = []
    for query, label in [("BAE Systems Holston Army Ammunition Plant explosive operator hiring", "Holston AAP"), ("Eurenco Bergerac explosive chemist", "Eurenco"), ("Chemring Nobel RDX chemist", "Chemring Nobel"), ("Rheinmetall explosive propellant engineer", "Rheinmetall"), ("Hanwha Corporation energetic materials", "Hanwha"), ("Solar Industries India explosive chemist", "Solar Industries")]:
        results = _brave_search(query, 3)
        found = len(results)
        signals.append({"query": label, "results_found": found, "status": "active_hiring" if found > 0 else "static"})
        if found:
            log(f"  {label}: {found} results (hiring signal)")
    out = {"status": "ok", "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "signals": signals}
    save_output("job-signals", out)
    return out

def collect_patents() -> dict:
    """Google Patents — RDX/HMX synthesis technology direction."""
    log("Checking RDX/HMX patent filings...")
    # Use Brave to find recent news about RDX patents
    items = _brave_search("RDX HMX insensitive munition patent 2025 2026", 5)
    patents = [{"title": item.get("title",""), "url": item.get("url","")} for item in items]
    out = {"status": "ok", "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "patents_found": len(patents), "patents": patents}
    save_output("patents", out)
    return out

def collect_car() -> dict:
    """Conflict Armament Research — munitions tracing back to RDX producers."""
    log("Checking CAR for munitions tracing reports...")
    results = []
    try:
        import feedparser
        feed = feedparser.parse("https://www.conflictarm.com/feed/")
        for entry in feed.get("entries", [])[:10]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if any(k in title.lower() for k in ["rdx", "explosive", "munition", "propellant", "ammunition"]):
                results.append({"title": title, "url": link, "published": entry.get("published", "")})
        if not results:
            # Fallback to Brave
            items = _brave_search("Conflict Armament Research ammunition explosives report", 5)
            for item in items:
                results.append({"title": item.get("title",""), "url": item.get("url",""), "description": item.get("description","")[:200]})
    except Exception as e:
        log(f"  CAR: {e}")
        items = _brave_search("Conflict Armament Research ammunition explosives", 5)
        for item in items:
            results.append({"title": item.get("title",""), "url": item.get("url","")})
    out = {"status": "ok", "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "reports_found": len(results), "reports": results[:15]}
    save_output("car-reports", out)
    return out

def collect_trade_remedy() -> dict:
    """Trade-remedy actions on precursors — hexamine AD/CVD, ammonium nitrate."""
    log("Checking trade-remedy actions on precursors...")
    results = []
    for label, q in [("USITC hexamine", "hexamine antidumping USITC 2025 2026 Bakelite"), ("USITC ammonium nitrate", "ammonium nitrate antidumping USITC 2026"), ("EC defence trade", "European Commission defence explosives propellant regulation")]:
        items = _brave_search(q, 3)
        for item in items:
            results.append({"source": label, "title": item.get("title",""), "url": item.get("url",""), "description": item.get("description","")[:200]})
    out = {"status": "ok", "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(), "actions_found": len(results), "actions": results}
    save_output("trade-remedy", out)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="RDX/C4 supply market data collectors")
    ap.add_argument("--gdelt-daily", action="store_true", help="GDELT news sweep")
    ap.add_argument("--osint-daily", action="store_true", help="Telegram OSINT channels")
    ap.add_argument("--contracts-weekly", action="store_true", help="USAspending contracts")
    ap.add_argument("--filings-weekly", action="store_true", help="Corporate filings")
    ap.add_argument("--epa-tri", action="store_true", help="EPA toxic release data")
    ap.add_argument("--jobs", action="store_true", help="Job posting signals")
    ap.add_argument("--patents", action="store_true", help="Patent filings")
    ap.add_argument("--car", action="store_true", help="Conflict Armament Research")
    ap.add_argument("--trade-remedy", action="store_true", help="Trade remedy monitoring")
    ap.add_argument("--all-creative", action="store_true", help="All creative source collectors")
    ap.add_argument("--all-daily", action="store_true", help="All daily tasks")
    ap.add_argument("--compile", action="store_true", help="Compile market tracker")
    args = ap.parse_args()

    ran = False
    if args.gdelt_daily or args.all_daily:
        collect_gdelt_daily(); ran = True
    if args.osint_daily or args.all_daily:
        collect_osint_daily(); ran = True
    if args.contracts_weekly:
        collect_contracts_weekly(); ran = True
    if args.filings_weekly:
        collect_filings_weekly(); ran = True
    if args.epa_tri or args.all_creative:
        collect_epa_tri(); ran = True
    if args.jobs or args.all_creative:
        collect_jobs(); ran = True
    if args.patents or args.all_creative:
        collect_patents(); ran = True
    if args.car or args.all_creative:
        collect_car(); ran = True
    if args.trade_remedy or args.all_creative:
        collect_trade_remedy(); ran = True
    if args.compile or ran:
        compile_tracker()
    if not ran and not args.compile:
        ap.print_help()


if __name__ == "__main__":
    main()
