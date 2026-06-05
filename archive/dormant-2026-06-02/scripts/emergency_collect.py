#!/usr/bin/env python3
"""Self-contained emergency collector — no imports from collect.py, strict per-feed timeouts."""
import json, os, pathlib, sys, urllib.request, datetime, re, html, concurrent.futures, time
from collections import Counter
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent

# Feed lists (copied from collect.py to avoid importing)
WIRE_FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("FT World", "https://www.ft.com/world?format=rss"),
    ("The Guardian World", "https://www.theguardian.com/world/rss"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
    ("France 24 EN", "https://www.france24.com/en/rss"),
    ("DW News EN", "https://rss.dw.com/rdf/rss-en-world"),
    ("CNBC World", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"),
]

LOCAL_LANGUAGE_FEEDS = [
    ("Arab News", "https://www.arabnews.com/rss.xml", "en"),
    ("The New Arab", "https://www.newarab.com/rss.xml", "en"),
    ("TASS (English)", "https://tass.com/rss/v2.xml", "en"),
    ("Meduza (English)", "https://meduza.io/rss/en/all", "en"),
    ("Moscow Times", "https://www.themoscowtimes.com/rss/news", "en"),
    ("South China Morning Post", "https://www.scmp.com/rss/4/feed", "en"),
    ("Jerusalem Post", "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx", "en"),
    ("Le Monde (English)", "https://www.lemonde.fr/en/rss/une.xml", "en"),
    ("El País (Spanish)", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "es"),
    ("Corriere della Sera (IT)", "https://xml2.corriereobjects.it/rss/esteri.xml", "it"),
    ("Channel News Asia", "https://www.channelnewsasia.com/rssfeeds/8395986", "en"),
    ("Africanews", "https://www.africanews.com/feed/", "en"),
    ("African Business", "https://african.business/feed/", "en"),
    ("Premium Times (Nigeria)", "https://www.premiumtimesng.com/feed", "en"),
    ("Daily Maverick (SA)", "https://www.dailymaverick.co.za/rss/", "en"),
    ("Mada Masr (Egypt)", "https://www.madamasr.com/en/feed/", "en"),
    ("Hespress (Morocco)", "https://en.hespress.com/feed/", "en"),
    ("Radio Dabanga (Sudan)", "https://www.dabangasudan.org/en/feed", "en"),
    ("Balkan Insight", "https://balkaninsight.com/feed/", "en"),
    ("VSquare", "https://vsquare.org/feed/", "en"),
    ("OCCRP", "https://www.occrp.org/feed/", "en"),
    ("Bellingcat", "https://www.bellingcat.com/feed/", "en"),
    ("OSW Warsaw", "https://www.osw.waw.pl/en/feed", "en"),
    ("Denník N (Slovakia)", "https://dennikn.sk/feed/", "sk"),
    ("ERR News (Estonia)", "https://news.err.ee/feed/", "en"),
    ("Dagens Nyheter (Sweden)", "https://www.dn.se/rss/", "sv"),
    ("Aftenposten (Norway)", "https://www.aftenposten.no/rss/", "no"),
    ("Meduza", "https://meduza.io/rss/en/all", "en"),
    ("Kyiv Independent", "https://kyivindependent.com/feed/", "en"),
    ("ISS Africa", "https://issafrica.org/rss.xml", "en"),
    ("The Africa Report", "https://www.theafricareport.com/feed/", "en"),
    ("BBC Africa", "https://feeds.bbci.co.uk/news/world/africa/rss.xml", "en"),
    ("France24 Afrique", "https://www.france24.com/en/africa/rss", "en"),
    ("BBC Europe", "https://feeds.bbci.co.uk/news/world/europe/rss.xml", "en"),
    ("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "en"),
    ("BBC Asia", "https://feeds.bbci.co.uk/news/world/asia/rss.xml", "en"),
    ("BBC Latin America", "https://feeds.bbci.co.uk/news/world/latin_america/rss.xml", "en"),
    ("BBC US & Canada", "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml", "en"),
]

def fetch_feed(name, url, timeout=6):
    """Fetch an RSS feed with a hard timeout. Returns (name, [(title, summary, link, pub, source), ...]) or (name, None)."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as exec:
            future = exec.submit(_do_fetch, url)
            result = future.result(timeout=timeout)
        if not result:
            return (name, [])
        import feedparser
        f = feedparser.parse(result)
        items = []
        for entry in f.entries[:20]:
            title = html.unescape(getattr(entry, 'title', '') or '')
            summary = html.unescape((getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''))
            link = getattr(entry, 'link', '') or ''
            pub = getattr(entry, 'published', getattr(entry, 'updated', '')) or ''
            items.append((title, summary[:600], link, pub, name))
        return (name, items)
    except concurrent.futures.TimeoutError:
        return (name, [])
    except Exception:
        return (name, [])

def _do_fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'TrevorIntel/1.0'})
    return urllib.request.urlopen(req, timeout=5).read()

def classify_region(title, summary, link):
    """Classify content into a region."""
    text = (title + " " + summary + " " + link).lower()
    regions = {
        "europe": ["ukraine", "russia", "europe", "eu", "nato", "uk", "britain", "france", "germany", 
                   "poland", "baltic", "balkan", "sweden", "norway", "denmark", "finland", "spain", "italy",
                   "hungary", "czech", "slovakia", "romania", "bulgaria", "greece", "cyprus", "croatia",
                   "belgium", "netherlands", "austria", "switzerland", "portugal", "ireland",
                   "westminster", "elysee", "bundestag", "kremlin", "putin", "zelensky"],
        "middle_east": ["iran", "iraq", "israel", "palestine", "gaza", "hezbollah", "houthi", "yemen",
                        "syria", "lebanon", "saudi", "uae", "qatar", "oman", "bahrain", "hormuz",
                        "irgc", "tehran", "khamenei", "gulf", "iraqi"],
        "north_america": ["united states", "canada", "mexico", "trump", "biden", "congress",
                          "white house", "pentagon", "fbi", "cia", "state department",
                          "washington", "new york", "wall street", "federal reserve"],
        "sub_saharan_africa": ["nigeria", "kenya", "ethiopia", "south africa", "ghana", "senegal",
                               "drc", "congo", "angola", "mozambique", "zimbabwe", "uganda", "rwanda",
                               "tanzania", "somalia", "sudan", "mali", "burkina", "niger", "chad",
                               "cameroon", "wagner", "africa corps"],
        "north_africa": ["morocco", "algeria", "tunisia", "libya", "egypt", "mauritania", "maghreb",
                         "sahel", "hespress", "mada masr"],
        "south_asia": ["india", "pakistan", "bangladesh", "sri lanka", "nepal", "afghanistan",
                        "kashmir", "modi", "new delhi"],
        "east_asia": ["china", "taiwan", "japan", "south korea", "north korea", "mongolia",
                       "beijing", "shanghai", "taipei", "seoul", "pyongyang",
                       "south china sea", "taiwan strait"],
        "south_east_asia": ["indonesia", "philippines", "vietnam", "thailand", "malaysia",
                            "singapore", "myanmar", "cambodia", "laos", "asean"],
        "central_america_caribbean": ["guatemala", "honduras", "el salvador", "nicaragua",
                                       "costa rica", "panama", "cuba", "haiti", "dominican",
                                       "jamaica", "puerto rico", "central america"],
        "south_america": ["brazil", "argentina", "colombia", "chile", "peru", "venezuela",
                          "ecuador", "bolivia", "paraguay", "uruguay", "lula", "maduro",
                          "amazon", "latin america"],
        "oceania": ["australia", "new zealand", "fiji", "papua new guinea", "pacific"],
        "central_asia": ["kazakhstan", "kyrgyzstan", "tajikistan", "turkmenistan", "uzbekistan"],
        "prediction_markets": ["kalshi", "polymarket", "oil price", "brent", "stock", "market",
                                "inflation", "rate hike", "yield", "sanction", "tariff",
                                "futures", "treasury"],
    }
    scores = {}
    for region, keywords in regions.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[region] = score
    if scores:
        return max(scores, key=scores.get)
    return None

def main():
    wd = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "tmp" / "emergency"
    wd.mkdir(parents=True, exist_ok=True)
    (wd / "raw").mkdir(exist_ok=True)
    (wd / "analysis").mkdir(exist_ok=True)
    
    print(f"[emergency] Collecting from {len(WIRE_FEEDS) + len(LOCAL_LANGUAGE_FEEDS)} feeds...", file=sys.stderr)
    
    all_feeds = [(n, u) for n, u in WIRE_FEEDS] + [(n, u) for n, u, *_ in LOCAL_LANGUAGE_FEEDS]
    
    # Fetch all feeds in parallel with per-feed timeout
    all_items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_feed, n, u): n for n, u in all_feeds}
        for future in concurrent.futures.as_completed(futures, timeout=90):
            name = futures[future]
            try:
                _, items = future.result()
                if items:
                    all_items.extend(items)
                    print(f"  ✅ {name}: {len(items)} items", file=sys.stderr)
                else:
                    print(f"  ⚠️ {name}: no items", file=sys.stderr)
            except Exception as e:
                print(f"  ❌ {name}: {str(e)[:60]}", file=sys.stderr)
    
    print(f"\n[emergency] Total items: {len(all_items)}", file=sys.stderr)
    
    # Classify by region
    incidents = []
    cutoff = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=48)).isoformat()
    
    for title, summary, link, pub, source in all_items:
        region = classify_region(title, summary, link)
        if not region:
            continue
        import hashlib
        inc_id = hashlib.md5((title + link).encode()).hexdigest()[:16]
        pub_str = pub[:10] if pub else cutoff[:10]
        
        # Filter financial vs security relevance
        text = (title + " " + summary).lower()
        financial_only = not any(kw in text for kw in [
            "attack", "kill", "strike", "missile", "drone", "military", "war", "conflict",
            "protest", "election", "sanction", "crime", "arrest", "prison", "court",
            "diplomat", "treaty", "negotiation", "nuclear", "ceasefire", "rebel",
            "jihad", "cartel", "gang", "kidnap", "explosion", "assault"
        ])
        
        incidents.append({
            "id": inc_id,
            "region": region if not financial_only else "prediction_markets",
            "country": "",
            "occurred_at": pub_str,
            "category": "security" if not financial_only else "finance",
            "headline": title[:200],
            "summary": summary[:600],
            "url": link,
            "sources": [{"name": source, "url": link, "reliability": "B", "credibility": 2}],
            "admiralty": ("B", 2),
        })
    
    # Save
    inc_path = wd / "raw" / "incidents.json"
    inc_path.write_text(json.dumps({"incidents": incidents}, indent=2))
    
    region_counts = Counter(i["region"] for i in incidents)
    print(f"\n[emergency] Saved {len(incidents)} incidents", file=sys.stderr)
    print("By region:", file=sys.stderr)
    for r, c in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"  {r}: {c}", file=sys.stderr)
    
    # Output JSON for pipeline consumption
    print(json.dumps({"incidents": len(incidents), "by_region": dict(region_counts)}))

if __name__ == "__main__":
    main()
