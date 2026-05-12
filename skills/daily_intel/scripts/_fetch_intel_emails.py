#!/usr/bin/env python3
"""Fetch raw intelligence emails from Gmail by label, routed by theatre.

Caches to temp for repeated reads during generation.
Usage: python3 _fetch_intel_emails.py [--force-fetch] [--output-dir /tmp/intel_raw]

Returns: dict of theatre -> [list of {subject, from, body, source}]
"""
import os, sys, json, base64, urllib.request, urllib.parse, datetime
from pathlib import Path

# Theatre routing rules: (keyword in subject OR sender) -> theatre key
ROUTING_RULES = [
    # Middle East / Iran (broad keywords to catch before ISW sender match routes to europe)
    ([
        "iran update", "iran war", "iran ceasefire", "strait of hormuz",
        "project freedom", "epic fury", "brent crude", "hormuz",
        "iran nuclear", "iran deal", "npt agreement", "iran democracy",
        "iran election", "pahlavi", "khamenei", "irgc",
        "middle east", "gaza", "hezbollah", "houthi", "yemen",
        "red sea", "uae attack", "uae strike", "fujairah",
        "iraq", "syria", "lebanon",
        # Catch-all for Iran-related ISW/CTP reports
        "iraq", "iran containment",
    ],
     ["CTP Publications", "criticalthreats@aei.org"],
     "middle_east"),
    # Europe / Russia-Ukraine
    (["russian offensive", "russia/ukraine", "ukraine update", "russia ceasefire",
      "ukraine ceasefire", "zelensky", "kremlin", "kyiv", "donbas", "pokrovsk",
      "kupyansk", "kostyantynivka", "ukrainian strike", "russian strike",
      "victory day", "mosfilm", "glonass", "black sea", "crimea",
      "russia resettlement", "occupied ukraine", "ukraine special report"],
     ["ISW Publications", "understandingwar.org"],
     "europe"),
    # Africa / Sahel
    (["sahel", "jnim", "mali", "burkina faso", "niger", "lake chad",
      "aes", "ecowas", "g5 sahel", "boko haram", "isgs", "iswap",
      "somalia", "al-shabaab", "ethiopia", "amhara", "tigray",
      "sudan", "rsf", "darfur", "congo", "car", "rwanda", "m23",
      "west africa", "east africa", "horn of africa"],
     [],
     "africa"),

    # Asia / Indo-Pacific
    (["north korea", "south korea", "korean peninsula", "kim jong",
      "icbm", "nuclear test", "nuclear warhead", "iaf sindoor",
      "india pakistan", "kashmir", "loac", "sindoor anniversary",
      "chinese", "china taiwan", "taiwan strait", "south china sea",
      "japan china", "east china sea", "philippines", "australia",
      "indo-pacific", "quad", "myanmar", "burma", "afghanistan",
      "indian ocean", "sri lanka"],
     [],
     "asia"),

    # North America
    (["mexico", "sinaloa", "cartel", "cártel", "cfe", "pemex",
      "us-mexico", "border security", "fentanyl", "drug trafficking",
      "treasury sanction", "ofac", "cisa", "cybersecurity",
      "critical infrastructure", "vulnerability bulletin",
      "homeland security", "nato", "nato/eu", "starmer",
      "uk election", "macron", "france", "germany", "scholz",
      "canada", "trudeau", "poilievre"],
     [],
     "north_america"),

    # South America
    (["venezuela", "maduro", "caracas", "miraflores", "guaidó",
      "colombia", "farc", "eln", "ecuador", "peru", "bolivia",
      "chile", "argentina", "milei", "brasil", "brazil", "lula",
      "amazon", "patagonia", "andes", "panama", "costa rica",
      "nicaragua", "orci", "cuba", "haiti"],
     [],
     "south_america"),

    # Global Finance
    (["oil price", "brent", "wti", "crude", "opec", "iea",
      "inflation", "fed", "federal reserve", "interest rate",
      "treasury yield", "dollar index", "commodity", "gdp",
      "equity market", "stock market", "emerging market",
      "sanctions", "trade war", "tariff", "supply chain",
      "prediction market", "polymarket", "kalshi", "forecast",
      "probability", "market pricing", "risk premium",
      "energy price", "gas price", "refinery"],
     [],
     "global_finance"),
]

# Catch-all: route by sender domain
DOMAIN_ROUTES = {
    "understandingwar.org": "europe",
    "criticalthreats@aei.org": "middle_east",
    "foreignpolicy.com": "global_finance",
    "thecipherbrief.com": "global_finance",
    "cisa.gov": "north_america",
    "cisa@messages.cisa.gov": "north_america",
}

LABEL_QUERY = "label:Intelligence"
GMAIL_API = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"
CACHE_DIR = Path("/tmp/daily_intel_emails")


def get_maton_key():
    """Read MATON_API_KEY from env or workspace .env."""
    key = os.environ.get("MATON_API_KEY", "")
    if not key:
        env_path = os.path.expanduser("~/.openclaw/workspace/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("MATON_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
    return key


def route_email(subject, sender):
    """Route an email to the correct theatre key."""
    subj_lower = (subject or "").lower()
    sender_lower = (sender or "").lower()
    
    for keywords, senders, theatre in ROUTING_RULES:
        for kw in keywords:
            if kw in subj_lower:
                return theatre
        for s in senders:
            if s.lower() in sender_lower:
                return theatre
    
    # Check domain routes
    for domain, theatre in DOMAIN_ROUTES.items():
        if domain.lower() in sender_lower:
            return theatre
    
    return "global_finance"  # default fallback


def extract_body(part):
    """Extract plain text body from email parts."""
    mt = part.get("mimeType", "")
    if mt == "text/plain" and part.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    if mt.startswith("multipart/"):
        texts = []
        for sp in part.get("parts", []):
            result = extract_body(sp)
            if result:
                texts.append(result)
        return "\n".join(texts)
    # Also try text/html if no plain text
    if mt == "text/html" and part.get("body", {}).get("data"):
        html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # Very basic HTML to text
        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]
    return ""


def fetch_emails(force_fetch=False, max_emails=30, max_days=7):
    """Fetch recent intel emails from Gmail, cached. Returns dict theatre->[emails]."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "intel_emails.json"
    
    # Check cache age
    if not force_fetch and cache_file.exists():
        age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds()
        if age < 3600:  # Cache valid for 1 hour
            print(f"Using cached emails ({age:.0f}s old)", file=sys.stderr, flush=True)
            return json.loads(cache_file.read_text())
    
    api_key = get_maton_key()
    if not api_key:
        print("ERROR: MATON_API_KEY not available", file=sys.stderr)
        return {}
    
    print(f"Fetching up to {max_emails} intel emails from Gmail...", file=sys.stderr, flush=True)
    
    # Calculate date filter
    after_date = (datetime.date.today() - datetime.timedelta(days=max_days)).isoformat()
    query = f"{LABEL_QUERY} after:{after_date}"
    
    url = f"{GMAIL_API}/messages?q={urllib.parse.quote(query)}&maxResults={max_emails}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"Gmail search failed: {e}", file=sys.stderr)
        return {}
    
    msg_list = data.get("messages", [])
    print(f"Found {len(msg_list)} messages", file=sys.stderr, flush=True)
    
    # Group by theatre
    by_theatre = {t["key"]: [] for t in [
        {"key": "europe"}, {"key": "africa"}, {"key": "asia"},
        {"key": "middle_east"}, {"key": "north_america"},
        {"key": "south_america"}, {"key": "global_finance"},
    ]}
    
    for m in msg_list:
        msg_id = m["id"]
        url2 = f"{GMAIL_API}/messages/{msg_id}"
        req2 = urllib.request.Request(url2)
        req2.add_header("Authorization", f"Bearer {api_key}")
        
        try:
            resp2 = urllib.request.urlopen(req2, timeout=30)
            msg = json.loads(resp2.read())
        except Exception:
            continue
        
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        date_str = headers.get("Date", "")
        
        body = extract_body(msg["payload"])
        if len(body) < 200:
            continue  # Skip emails with no substantial content
        
        # Skip marketing/promotional emails
        promo_keywords = ["subscribe now", "67% off", "exclusive offer", "act now",
                         "limited time", "special offer", "sale ends", "view in browser",
                         "manage your preferences", "unsubscribe"]
        subj_lower_check = (subject or "").lower()
        if any(kw in subj_lower_check for kw in promo_keywords):
            continue
        
        # Truncate very long bodies
        body = body[:6000]
        
        theatre = route_email(subject, sender)
        
        entry = {
            "subject": subject,
            "from": sender,
            "date": date_str[:30],
            "body": body[:5000],
            "source": sender.split("<")[-1].rstrip(">") if "<" in sender else sender,
        }
        
        if theatre in by_theatre:
            by_theatre[theatre].append(entry)
        else:
            by_theatre["global_finance"].append(entry)
    
    # Sort each theatre by date (newest first), limit to top 5 per theatre
    for theatre in by_theatre:
        by_theatre[theatre].sort(key=lambda x: x.get("date", ""), reverse=True)
        by_theatre[theatre] = by_theatre[theatre][:5]
    
    # Count and report
    total = sum(len(v) for v in by_theatre.values())
    print(f"Cached {total} emails across {len([t for t in by_theatre if by_theatre[t]])} theatres", file=sys.stderr, flush=True)
    
    # Write cache
    cache_file.write_text(json.dumps(by_theatre, indent=2))
    
    return by_theatre


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-fetch", action="store_true")
    parser.add_argument("--max-emails", type=int, default=30)
    args = parser.parse_args()
    
    emails = fetch_emails(force_fetch=args.force_fetch, max_emails=args.max_emails)
    for theatre, entries in sorted(emails.items()):
        if entries:
            print(f"\n{theatre.upper()}: {len(entries)} emails")
            for e in entries:
                print(f"  {e['subject'][:80]}")
                print(f"    Source: {e['source'][:40]}")
