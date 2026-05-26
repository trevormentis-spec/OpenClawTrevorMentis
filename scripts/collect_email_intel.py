#!/usr/bin/env python3
"""
Collect email intel from Gmail + AgentMail, inject into working directory.

Reads:
  - Gmail inbox (trevor.mentis@gmail.com) via Maton API — ISW, CTP, Cipher Brief, FP
  - AgentMail inbox (trevor_mentis@agentmail.to) via AgentMail API

Converts both into the orchestrator's incident format and injects into
WORKING_DIR/raw/incidents.json under a special "email_intel" source category.

Usage:
    python3 scripts/collect_email_intel.py --working-dir ~/trevor-briefings/2026-05-21
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

MATON_BASE = "https://gateway.maton.ai/google-mail"
GMAIL_LIST = MATON_BASE + "/gmail/v1/users/me/messages"
GMAIL_GET = MATON_BASE + "/gmail/v1/users/me/messages/{}"

AGENTMAIL_BASE = "https://api.agentmail.to/v0/inboxes/trevor_mentis@agentmail.to/messages"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"

# Which Gmail senders count as "intelligence sources" — specific named sources get
# preferential routing to their primary region
INTEL_SENDERS = [
    "criticalthreats@aei.org",          # CTP/ISW
    "publications@understandingwar.org", # ISW
    "dailybrief@thecipherbrief.com",    # Cipher Brief
    "newsletters@foreignpolicy.com",    # Foreign Policy
    "news@mail.mapbox.com",             # Mapbox (geospatial intel)
    "foreignpolicy.com",                # FP fallback
    "newsletters@breakingdefense.com",   # Breaking Defense
    "communications@cfr.org",           # CFR
    "news@hudson.org",                  # Hudson Institute
    "aei_today@aei.org",                # AEI
    "nytdirect@nytimes.com",            # NYT
    "noreply@news.bloomberg.com",       # Bloomberg
    "politicoplaybook@email.politico.com", # POLITICO
    "info@info.politico.com",           # POLITICO
    "mike@axios.com",                   # Axios
    "barak.ravid@axios.com",            # Axios
    "no-reply@substack.com",            # Substack newsletters
]

# Sender-based region routing — known newsletters get routed to their primary region
# regardless of keyword matching. This catches newsletters that are thematically broad
# but cover specific regional beats.
SENDER_REGION_MAP = {
    # Middle East beat
    "barak.ravid@axios.com": "middle_east",
    # Defense/security → global, but Breaking Defense leans Middle East + Europe
    "newsletters@breakingdefense.com": "middle_east",
    # Foreign policy think tanks
    "communications@cfr.org": "north_america",
    "news@hudson.org": "north_america",
    "aei_today@aei.org": "north_america",
    "newsletters@foreignpolicy.com": "north_america",
    # Major news — broad coverage, classify by content
    "nytdirect@nytimes.com": None,  # keyword-classify
    "noreply@news.bloomberg.com": None,  # keyword-classify
    "politicoplaybook@email.politico.com": "north_america",
    "info@info.politico.com": "north_america",
    "mike@axios.com": "north_america",
    # Substack: classify by content
    "no-reply@substack.com": None,
    # Specific intel feeds
    "publications@understandingwar.org": "europe",  # ISW primarily Ukraine/Russia
    "criticalthreats@aei.org": "middle_east",  # CTP primarily Middle East
}

# Region keywords for classification
REGION_KEYWORDS = {
    "middle_east": ["iran", "israel", "gaza", "hezbollah", "houthi", "hormuz",
                    "syria", "iraq", "lebanon", "yemen", "gulf", "qatar", "saudi",
                    "uae", "oman", "bahrain", "kuwait", "strike", "centcom"],
    "europe": ["europe", "eu", "nato", "ukraine", "russia", "britain", "france",
               "germany", "poland", "baltic", "latvia", "estonia", "lithuania",
               "sweden", "finland", "norway", "denmark", "netherlands",
               "brussels", "european union"],
    "north_america": ["united states", "usa", "canada", "mexico", "us-mexico", "trump",
                      "white house", "congress", "pentagon", "state department",
                      "border", "cartel", "fentanyl"],
    "central_america_caribbean": ["guatemala", "honduras", "el salvador", "nicaragua",
                                  "costa rica", "panama", "cuba", "haiti", "dominican",
                                  "jamaica", "central america", "caribbean"],
    "south_america": ["brazil", "argentina", "colombia", "chile", "peru",
                      "venezuela", "ecuador", "latin america", "amazon",
                      "lula", "maduro", "bolivia", "paraguay", "uruguay"],
    "north_africa": ["north africa", "maghreb", "egypt", "libya", "algeria", "morocco", "tunisia", "sahel"],
    "sub_saharan_africa": ["sub-saharan africa", "west africa", "east africa", "nigeria", "kenya", "ethiopia", "south africa"]}
               "libya", "algeria", "morocco", "tunisia", "sudan", "somalia",
               "ethiopia", "ghana", "angola", "mozambique", "au", "african union",
               "nile", "sahel", "maghreb"],
    "central_asia": ["china", "india", "japan", "south korea", "north korea",
                     "russia", "putin", "kazakhstan", "pakistan", "afghanistan",
                     "mongolia", "armenian", "azerbaijan", "georgia",
                     "south china sea", "spratly", "senkaku", "diaoyu", "quad"],
    "south_east_asia": ["myanmar", "thailand", "vietnam", "indonesia", "philippines",
                        "malaysia", "singapore", "cambodia", "laos", "brunei",
                        "timor", "sri lanka", "bangladesh", "nepal", "bhutan",
                        "mekong", "asean"],
    "oceania": ["australia", "new zealand", "fiji", "papua new guinea", "taiwan",
                "pacific islands", "oceania", "solomon islands", "vanuatu",
                "samoa", "tonga"],
    "prediction_markets": ["oil", "brent", "wti", "lng", "energy", "sanctions",
                           "tariff", "trade", "stock market", "fed", "interest rate",
                           "inflation", "supply chain", "semiconductor", "chip",
                           "crypto", "bitcoin", "treasury", "dollar", "yuan",
                           "kalshi", "polymarket", "prediction market"],
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[email_intel {ts}] {msg}", file=sys.stderr, flush=True)


def get_maton_key() -> str:
    """Get Maton API key from env or .env."""
    key = os.environ.get("MATON_API_KEY", "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if line.strip().startswith("MATON_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def get_agentmail_key() -> str:
    """Get AgentMail API key."""
    for env_var in ["AGENTMAIL_API_KEY", "AGENTMAIL_TOKEN"]:
        key = os.environ.get(env_var, "")
        if key:
            return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if "AGENTMAIL" in line and "=" in line:
                return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def classify_region(text: str, from_addr: str = "") -> str:
    """Classify which region an email belongs to.
    
    Checks sender-based routing first (SENDER_REGION_MAP), then falls
    back to keyword matching against REGION_KEYWORDS.
    """
    # 1. Sender-based routing (fast, accurate for known sources)
    if from_addr:
        # Normalize the from address — extract just the email
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', from_addr)
        clean_addr = email_match.group(0).lower() if email_match else from_addr.lower()
        if clean_addr in SENDER_REGION_MAP:
            mapped = SENDER_REGION_MAP[clean_addr]
            if mapped is not None:
                return mapped

    # 2. Keyword-based classification (fallback)
    text_lower = text.lower()
    scores = {}
    for region, keywords in REGION_KEYWORDS.items():
        scores[region] = sum(1 for kw in keywords if kw in text_lower)
    if max(scores.values()) == 0:
        return "global_finance"  # default
    return max(scores, key=scores.get)


def make_incident_id(subject: str, from_addr: str) -> str:
    """Create a deterministic incident ID."""
    raw = f"email-{from_addr}-{subject}"
    return "em-" + hashlib.md5(raw.encode()).hexdigest()[:8]


def fetch_gmail_intel(maton_key: str, max_msgs: int = 15) -> list[dict]:
    """Fetch recent intelligence emails from Gmail."""
    if not maton_key:
        log("No MATON_API_KEY — skipping Gmail")
        return []

    # Search for intel emails from last 48h
    import urllib.parse
    two_days_ago = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).strftime("%Y/%m/%d")
    # Build sender filter from INTEL_SENDERS
    sender_filter = " OR ".join(f"from:({s})" for s in INTEL_SENDERS[:10])
    q = urllib.parse.quote(f"{{{sender_filter}}} after:{two_days_ago}")
    url = f"{GMAIL_LIST}?q={q}&maxResults={max_msgs}"

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {maton_key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            messages = json.loads(resp.read()).get("messages", [])
    except Exception as e:
        log(f"Gmail list failed: {e}")
        return []

    incidents = []
    for msg in messages[:max_msgs]:
        msg_id = msg.get("id", "")
        req2 = urllib.request.Request(
            GMAIL_GET.format(msg_id),
            headers={"Authorization": f"Bearer {maton_key}"},
        )
        try:
            with urllib.request.urlopen(req2, timeout=10) as resp:
                detail = json.loads(resp.read())
        except Exception:
            continue

        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "No Subject")
        from_addr = headers.get("From", "unknown@unknown.com")
        # Extract first ~500 chars of body
        body = ""
        payload = detail.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    import base64
                    try:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    except Exception:
                        pass
                    break
            if not body:
                for part in payload["parts"]:
                    if part.get("mimeType", "").startswith("text/"):
                        try:
                            body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                        break

        full_text = f"{subject} {body[:2000]}"
        region = classify_region(full_text, from_addr)

        incident = {
            "id": make_incident_id(subject, from_addr),
            "region": region,
            "country": "multi",
            "source": "gmail_intel",
            "occurred_at_utc": headers.get("Date", dt.datetime.now(dt.timezone.utc).isoformat()),
            "category": "intelligence_email",
            "headline": subject[:120],
            "summary": body[:500] if body else "Email body not extracted",
            "sources": [{"name": f"Gmail: {from_addr}", "url": f"email://{from_addr}"}],
        }
        incidents.append(incident)
        log(f"Gmail: {subject[:60]} → {region}")

    return incidents


def fetch_agentmail_intel(api_key: str, max_msgs: int = 15) -> list[dict]:
    """Fetch recent messages from AgentMail inbox."""
    if not api_key:
        log("No AGENTMAIL_API_KEY — skipping AgentMail")
        return []

    req = urllib.request.Request(
        f"{AGENTMAIL_BASE}?limit={max_msgs}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        log(f"AgentMail list failed: {e}")
        return []

    messages = data.get("messages", data if isinstance(data, list) else [])
    incidents = []

    for msg in messages:
        if isinstance(msg, dict):
            from_addr = ""
            sender = msg.get("from", {})
            if isinstance(sender, dict):
                from_addr = sender.get("email", "unknown@agentmail")
            elif isinstance(sender, str):
                from_addr = sender

            subject = msg.get("subject", "No Subject")
            body = msg.get("text_body", msg.get("body", ""))[:2000]

            # Skip self-sent emails (Trevor's own brief deliveries, reports, etc.)
            # These are output, not intelligence input
            if "trevor_mentis@agentmail.to" in from_addr.lower() or \
               "trevor.mentis@gmail.com" in from_addr.lower():
                continue

            full_text = f"{subject} {body}"
            region = classify_region(full_text, from_addr)

            incident = {
                "id": make_incident_id(subject, from_addr),
                "region": region,
                "country": "multi",
                "source": "agentmail_intel",
                "occurred_at_utc": msg.get("created_at", msg.get("timestamp", "")),
                "category": "intelligence_email",
                "headline": subject[:120],
                "summary": body[:500],
                "sources": [{"name": f"AgentMail: {from_addr}", "url": f"email://{from_addr}"}],
            }
            incidents.append(incident)
            log(f"AgentMail: {subject[:60]} → {region}")

    return incidents


def inject_into_working_dir(incidents: list[dict], working_dir: pathlib.Path) -> int:
    """Inject email intel incidents into the working directory's raw data."""
    incidents_file = working_dir / "raw" / "incidents.json"
    if not incidents_file.exists():
        log(f"No incidents.json found at {incidents_file} — creating")
        working_dir.joinpath("raw").mkdir(parents=True, exist_ok=True)
        incidents_file.write_text(json.dumps({
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "window_hours": 48,
            "regions_covered": list(list(REGION_KEYWORDS.keys())),
            "incidents": [],
            "collection_gaps": [],
        }, indent=2))

    try:
        data = json.loads(incidents_file.read_text())
    except (json.JSONDecodeError, Exception):
        data = {"incidents": []}

    existing_ids = {i.get("id", "") for i in data.get("incidents", [])}
    new_count = 0
    for inc in incidents:
        if inc["id"] not in existing_ids:
            data.setdefault("incidents", []).append(inc)
            existing_ids.add(inc["id"])
            new_count += 1

    data["generated_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    incidents_file.write_text(json.dumps(data, indent=2))
    log(f"Injected {new_count} email intel incidents into {incidents_file}")
    return new_count


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Collect email intel from Gmail + AgentMail")
    parser.add_argument("--working-dir", required=True, help="Path to trevor-briefings date dir")
    parser.add_argument("--max", type=int, default=15, help="Max emails per inbox")
    args = parser.parse_args()

    working_dir = pathlib.Path(args.working_dir).expanduser().resolve()
    maton_key = get_maton_key()
    agentmail_key = get_agentmail_key()

    if not maton_key and not agentmail_key:
        log("ERROR: Neither MATON_API_KEY nor AGENTMAIL_API_KEY set")
        print("WARNING: No email intel collected — no API keys available")
        return

    all_incidents = []

    # Fetch Gmail
    if maton_key:
        log("Fetching Gmail intel...")
        gmail_incs = fetch_gmail_intel(maton_key, args.max)
        all_incidents.extend(gmail_incs)
        log(f"  → {len(gmail_incs)} Gmail incidents")

    # Fetch AgentMail
    if agentmail_key:
        log("Fetching AgentMail intel...")
        agentmail_incs = fetch_agentmail_intel(agentmail_key, args.max)
        all_incidents.extend(agentmail_incs)
        log(f"  → {len(agentmail_incs)} AgentMail incidents")

    # Also read from tasks/news_raw.md if it exists (already fetched by cron)
    news_raw = TASKS_DIR / "news_raw.md"
    if news_raw.exists():
        text = news_raw.read_text()
        # Parse markdown sections as incidents
        sections = re.split(r"^## ", text, flags=re.MULTILINE)
        for section in sections[1:]:  # Skip the header
            lines = section.strip().split("\n")
            headline = lines[0].strip()
            full = section[:2000]
            # Extract "From:" line before classification
            from_match = re.search(r"\*\*From:\*\* (.+)", section)
            from_addr = from_match.group(1) if from_match else "newsletter@intel"
            region = classify_region(full, from_addr)

            inc = {
                "id": make_incident_id(headline, from_addr),
                "region": region,
                "country": "multi",
                "source": "gmail_intel_digest",
                "occurred_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "category": "intelligence_email",
                "headline": headline[:120],
                "summary": full[:500],
                "sources": [{"name": f"Gmail Digest: {from_addr}", "url": f"email://{from_addr}"}],
            }
            all_incidents.append(inc)

        log(f"  → {len(sections)-1} from news_raw.md digest")

    # Inject
    if all_incidents:
        count = inject_into_working_dir(all_incidents, working_dir)
        print(f"Email intel: {count} new incidents injected into working dir")
        log(f"Total: {count} new from {len(all_incidents)} raw emails")
    else:
        print("Email intel: No new incidents found")
        log("No email intel found")


if __name__ == "__main__":
    main()
