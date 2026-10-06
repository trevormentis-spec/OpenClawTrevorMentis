#!/usr/bin/env python3
"""
AgentMail Reader — fetches recent messages and injects intel into news_raw.md.
Silent pipeline feeder. Mirrors gmail_reader.py behavior for AgentMail inbox.

Usage:
    python3 scripts/agentmail_reader.py --max 10 --save
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_NEWS_FILE = REPO_ROOT / "tasks" / "news_raw.md"
PROCESSED_IDS_FILE = REPO_ROOT / "brain" / "working-memory" / "agentmail-processed-ids.json"
MAX_PROCESSED_IDS = 500

# Noise senders — these are NOT intelligence content and should be filtered out
# before writing to news_raw.md. Pruned 2026-08-15 against actual inbox traffic
# (2,328 msgs / 207 senders). Kept all intel-relevant senders (CSIS, RAND, Hudson,
# Brookings, AEI, Cato, CNAS, Lawfare, War on the Rocks, Breaking Defense,
# SpaceNews, Payload, Data Center Frontier, Kyiv Independent, InSight Crime, ISS
# Africa, ChinaTalk, Sinocism, GZERO, Canary Media, Seatrade, etc.).
NOISE_SENDERS = [
    # --- NYT family (only the noise/lifestyle/marketing variants) ---
    "wirecutter@nytimes.com",           # Product recommendations
    "nytdirect@nytimes.com",            # NYT newsletters (Morning, etc.)
    "editorpicks@nytimes.com",          # NYT Editor Picks (news digest)
    "yourplaces-globalupdate",          # NYT Your Places (travel/lifestyle)
    "nyt@e.nytimes.com",                # NYT marketing
    "nytimes@e.newyorktimes.com",       # NYT marketing
    # --- Bloomberg (all variants) ---
    "bloomberg.com",                    # Any Bloomberg newsletter
    "citylab@bloomberg.com",            # CityLab
    # --- POLITICO gossip (NatSec Daily stays — it's intel) ---
    "politicoplaybook",                 # Playbook + Playbook PM (DC insider gossip)
    "info.politicopro.com",             # POLITICO Pro marketing
    "events@live.politico.com",         # POLITICO Live event promos
    # --- Finance/trading digests (not intel) ---
    "execsum.co",                       # Exec Sum - Litquidity
    "cryptosum@mail.beehiiv.com",       # Crypto Sum - Litquidity
    "schiffsovereign",                  # Schiff Sovereign (goldbug economics)
    "robotwealth.com",                  # Kris / Robot Wealth
    "institutionalinvestor.com",        # Essential II (Institutional Investor)
    "kalshi@mail",                      # Kalshi market promos (scanner covers this)
    # --- Insurance/reinsurance trade rags (not intel) ---
    "reinsurancene.ws",                 # Reinsurance News
    "artemis.bm",                       # Artemis (cat bonds)
    "insuranceinsider.com",             # Insurance Insider
    # --- Tech digest noise ---
    "tldrnewsletter.com",               # TLDR + TLDR AI
    # --- Platform/marketing noise ---
    "no-reply@substack.com",            # Substack platform notifications
    "no-reply@info.patreon.com",        # Patreon platform notifications
    "no-reply@updates.patreon.com",     # Patreon platform notifications
    "aila@csis.org",                    # CSIS Executive Education promos
    "externalrelations@csis.org",       # CSIS External Relations promos
    "events@mei.edu",                   # MEI event invitations
    "events@hudson.org",                # Hudson event invitations
    "events@brookings.edu",             # Brookings events
    "events@spacenews.com",             # SpaceNews events
    "events@news.payloadspace.com",     # Payload events
    "events@latitudemedia.com",         # Latitude events
    "customer.care@theafricareport.com",# The Africa Report marketing (content sender stays)
    "breaking defense - webinar",       # Breaking Defense webinar promos
    "breaking defense webinar",         # Breaking Defense Webinar (no hyphen variant)
    "webinar",                          # Any other webinar promo sender
    "medium.com",                       # Medium digest
]

# Subject-line patterns that indicate non-intel content
NOISE_SUBJECT_PATTERNS = [
    r"Your (daily|weekly|morning) (briefing|digest|roundup|newsletter)",
    r"Deal[s]? of the (day|week)",
    r"Sponsored",
    r"Advertisement",
]

def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[agentmail-read {ts}] {msg}", file=sys.stderr, flush=True)

def load_processed_ids() -> set:
    """Load set of already-processed message IDs from state file."""
    if not PROCESSED_IDS_FILE.exists():
        return set()
    try:
        data = json.loads(PROCESSED_IDS_FILE.read_text())
        return set(data.get("processed_ids", []))
    except (json.JSONDecodeError, KeyError, OSError) as e:
        log(f"Could not load processed IDs: {e} — starting fresh")
        return set()


def save_processed_ids(processed: set) -> None:
    """Persist processed message IDs to state file.
    Keeps only the most recent MAX_PROCESSED_IDS entries."""
    # Keep only the last N (oldest entries dropped when we trim at save time)
    entries = list(processed)[-MAX_PROCESSED_IDS:]
    state = {
        "processed_ids": entries,
        "count": len(entries),
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    PROCESSED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_IDS_FILE.write_text(json.dumps(state, indent=2))


def get_api_key() -> str:
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("AGENTMAIL_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

def fetch_messages(api_key: str, max_msgs: int = 10) -> list[dict]:
    """Fetch recent messages from AgentMail inbox."""
    from agentmail import AgentMail
    client = AgentMail(api_key=api_key)
    try:
        inboxes = client.inboxes.list()
        trevor = inboxes.inboxes[0].inbox_id
        msgs = client.inboxes.messages.list(trevor, limit=max_msgs)
        results = []
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)
        for m in msgs.messages:
            created = m.created_at
            if hasattr(created, 'timestamp'):
                created_dt = dt.datetime.fromtimestamp(created.timestamp(), tz=dt.timezone.utc)
            elif isinstance(created, str):
                created_dt = dt.datetime.fromisoformat(created.replace('Z', '+00:00'))
            else:
                created_dt = created
            if created_dt < cutoff:
                continue
            # Skip outbound (sent by Trevor)
            from_addr = str(m.from_ or "")
            if "trevor" in from_addr.lower():
                continue

            # Skip noise senders
            subject = (m.subject or "(no subject)")
            is_noise = False
            for noise_sender in NOISE_SENDERS:
                if noise_sender in from_addr.lower():
                    log(f"Noise filter: skipping '{subject[:60]}' from {from_addr[:40]}")
                    is_noise = True
                    break
            if is_noise:
                continue

            # Skip noise subject patterns
            for pattern in NOISE_SUBJECT_PATTERNS:
                if re.search(pattern, subject, re.IGNORECASE):
                    log(f"Noise filter: skipping '{subject[:60]}' (subject pattern)")
                    is_noise = True
                    break
            if is_noise:
                continue

            mid = getattr(m, "message_id", "") or ""

            results.append({
                "message_id": mid,
                "from": from_addr,
                "subject": subject,
                "body": (m.preview or "")[:500],
                "created_at": str(m.created_at)[:19],
            })
        return results
    except Exception as e:
        log(f"Fetch failed: {e}")
        return []

def save_news_raw(messages: list[dict], processed: set) -> int:
    """Append only new (unseen) intel items to tasks/news_raw.md.
    Returns count of newly written items."""
    # Filter to only unseen messages
    new_messages = [m for m in messages if m.get("message_id", "") not in processed]

    if not new_messages:
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H:%M UTC")

    lines = []
    lines.append(f"\n## AgentMail Intel — {date_str} {ts}")
    lines.append("")

    for msg in new_messages:
        subject = msg.get("subject", "").strip()
        body = msg.get("body", "").strip()
        sender = msg.get("from", "unknown")
        mid = msg.get("message_id", "")
        lines.append(f"### {subject}")
        lines.append(f"**From:** {sender}  ")
        lines.append(f"*MsgID: {mid}*  ")
        if body:
            # Extract key sentences
            clean = re.sub(r'<[^>]+>', '', body)
            clean = re.sub(r'\s+', ' ', clean).strip()
            lines.append(clean[:600])
        lines.append("")

    content = "\n".join(lines)
    RAW_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_NEWS_FILE, "a") as f:
        f.write(content)

    # Mark as processed
    for msg in new_messages:
        processed.add(msg.get("message_id", ""))

    return len(new_messages)

def main():
    parser = argparse.ArgumentParser(description="AgentMail Reader — fetch and inject intel")
    parser.add_argument("--max", type=int, default=10, help="Max messages to fetch")
    parser.add_argument("--save", action="store_true", help="Save to news_raw.md")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        log("ERROR: AGENTMAIL_API_KEY not set")
        sys.exit(1)

    log(f"Fetching last {args.max} AgentMail messages...")
    messages = fetch_messages(api_key, args.max)
    log(f"Found {len(messages)} recent inbound messages")

    # Load processed message IDs so we can skip duplicates
    processed = load_processed_ids()
    log(f"Tracking {len(processed)} previously processed message IDs")

    # Filter to only new messages before any action
    new_messages = [m for m in messages if m.get("message_id", "") not in processed]
    skipped = len(messages) - len(new_messages)
    if skipped:
        log(f"Skipping {skipped} already-processed messages")

    if args.stdout:
        for msg in new_messages:
            print(f"\n### {msg['subject']}")
            print(f"From: {msg['from']}")
            print(f"Date: {msg['created_at']}")
            print(msg['body'][:300])
    elif args.save:
        saved = save_news_raw(new_messages, processed)
        if saved:
            log(f"Saved {saved} new items to {RAW_NEWS_FILE}")
            save_processed_ids(processed)
            log(f"Updated processed-IDs tracker ({len(processed)} entries)")
        else:
            log("No new messages to save")
    else:
        log("No action specified. Use --save or --stdout.")

    # Low-balance watchdogs: ride this existing hourly job (no new cron).
    # Non-fatal — never let a balance check break inbox ingestion.
    for watchdog in ("deepseek_balance_alert.py", "openrouter_balance_alert.py"):
        try:
            import subprocess
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / watchdog)],
                capture_output=True, text=True, timeout=60,
            )
            out = (proc.stdout or "").strip().splitlines()
            if out:
                log(f"balance watchdog ({watchdog}): {out[-1]}")
        except Exception as e:
            log(f"balance watchdog ({watchdog}) skipped: {e}")

if __name__ == "__main__":
    main()
