#!/usr/bin/env python3
"""
Fetch last 7 days of AgentMail and Gmail intel, compile for summary.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Auth helpers ──

def read_env(key: str) -> str:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get(key, "")

AM_KEY = read_env("AGENTMAIL_API_KEY")
MATON_KEY = read_env("MATON_API_KEY")
WEEK_AGO = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).isoformat() + "Z"

# ── AgentMail ──

def fetch_am_messages(limit: int = 100) -> list[dict]:
    """Fetch messages from AgentMail, returning list with subject/from/date/preview."""
    url = f"https://api.agentmail.to/v0/inboxes/trevor_mentis%40agentmail.to/messages?limit={limit}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AM_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[AM] Fetch error: {e}", file=sys.stderr)
        return []
    return data.get("messages", [])

def fetch_am_body(message_id: str) -> str:
    """Fetch full email body from AgentMail by message ID."""
    url = f"https://api.agentmail.to/v0/inboxes/trevor_mentis%40agentmail.to/messages/{urllib.request.quote(message_id, safe='')}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AM_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return f"[body fetch error: {e}]"
    # Extract text body (prefer plain text)
    body = data.get("text", data.get("html", data.get("preview", "")))
    if isinstance(body, str):
        return body[:5000]  # truncate to 5K chars
    return str(body)[:5000]

# ── Gmail via Maton ──

def fetch_gmail_messages(limit: int = 30) -> list[dict]:
    """Fetch Gmail messages from last 7 days."""
    q = f"after:{WEEK_AGO[:10]}"
    url = f"https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?maxResults={limit}&q={urllib.request.quote(q)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {MATON_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[Gmail] List error: {e}", file=sys.stderr)
        return []
    return data.get("messages", [])

def fetch_gmail_msg(msg_id: str) -> dict:
    url = f"https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}?format=full"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {MATON_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def decode_gmail_body(msg: dict) -> str:
    """Extract plain text from a Gmail message payload."""
    def _decode(data):
        alt = data.get("body", {}).get("data", "")
        if alt:
            import base64
            try:
                return base64.urlsafe_b64decode(alt).decode("utf-8", errors="replace")
            except Exception:
                return ""
        for part in data.get("parts", []):
            res = _decode(part)
            if res:
                return res
        return ""
    
    # Prefer text/plain
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            body = _decode(part)
            if body:
                return body[:5000]
    for part in parts:
        if part.get("mimeType") == "text/html":
            body = _decode(part)
            if body:
                return body[:5000]
    return _decode(payload)

def extract_header(msg: dict, name: str) -> str:
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""

# ── Main ──

def main():
    report_sections = []
    
    # === AGENTMAIL ===
    print("Fetching AgentMail messages...", file=sys.stderr)
    am_msgs = fetch_am_messages(100)
    am_week = [m for m in am_msgs if m.get("created_at", "") >= WEEK_AGO]
    print(f"  Found {len(am_week)} messages from last 7 days", file=sys.stderr)
    
    # Deduplicate by subject (often the same newsletters arrive)
    seen_subjects = set()
    unique_am = []
    for m in am_week:
        subj = m.get("subject", "").strip()
        if subj and subj not in seen_subjects:
            seen_subjects.add(subj)
            unique_am.append(m)
    
    am_entries = []
    for m in unique_am:
        mid = m.get("message_id", "")
        body = fetch_am_body(mid) if mid else ""
        text_clean = re.sub(r'<[^>]+>', '', body)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        am_entries.append({
            "from": m.get("from", "?"),
            "subject": m.get("subject", "?"),
            "date": m.get("created_at", "?")[:19],
            "body": text_clean[:2000],
        })
    
    report_sections.append(("agentmail", am_entries))
    
    # === GMAIL ===
    print("Fetching Gmail messages...", file=sys.stderr)
    gm_list = fetch_gmail_messages(30)
    print(f"  Found {len(gm_list)} messages", file=sys.stderr)
    
    gm_entries = []
    for i, gm in enumerate(gm_list[:25]):  # limit to 25
        msg_id = gm.get("id", "")
        full = fetch_gmail_msg(msg_id)
        if "error" in full:
            continue
        body_text = decode_gmail_body(full)
        body_clean = re.sub(r'<[^>]+>', '', body_text)
        body_clean = re.sub(r'\s+', ' ', body_clean).strip()
        gm_entries.append({
            "from": extract_header(full, "From"),
            "subject": extract_header(full, "Subject"),
            "date": extract_header(full, "Date"),
            "body": body_clean[:2000],
        })
    
    report_sections.append(("gmail", gm_entries))
    
    # ── Write output ──
    output = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "since": WEEK_AGO,
        "agentmail_count": len(am_entries),
        "gmail_count": len(gm_entries),
        "sections": [],
    }
    
    for source, entries in report_sections:
        output["sections"].append({
            "source": source,
            "entries": entries,
        })
    
    outpath = REPO_ROOT / "exports" / f"weekly-intel-{dt.date.today().isoformat()}.json"
    outpath.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nWritten to {outpath}", file=sys.stderr)
    print(f"AgentMail: {len(am_entries)} unique items", file=sys.stderr)
    print(f"Gmail: {len(gm_entries)} items", file=sys.stderr)

if __name__ == "__main__":
    main()
