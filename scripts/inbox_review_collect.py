#!/usr/bin/env python3
"""
Daily Inbox Review — collection stage.

Gathers the last N hours of AgentMail mail, flags Substack items, resolves canonical post
URLs, and fetches the post text so the review stage has real content to work from.

Writes: tasks/inbox-review-<date>.md   (raw material, structured for the reviewer)
        tasks/inbox-review-<date>.json (same, machine-readable)

This script does NO analysis — it only collects. The review/summary is produced downstream.

Usage
    python3 scripts/inbox_review_collect.py                 # last 24h
    python3 scripts/inbox_review_collect.py --hours 48
    python3 scripts/inbox_review_collect.py --hours 24 --max-fetch 10
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import pathlib
import re
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
ENV = REPO / ".env"
TASKS = REPO / "tasks"

SUBSTACK_HINTS = ("substack.com", "sinocism", "chinatalk.media", "newsletter.doomberg",
                  "stratechery", "timothygartonash", "oneusefulthing", "thegeneralist",
                  "notboring", "ryanmcbeth", "mikefroman", "osintnewsletter", "lawfare",
                  "importai", "interconnects")

# pure marketing / platform notifications we never want in the review
NOISE = ("no-reply@substack.com", "nytdirect@nytimes.com", "editorpicks@nytimes.com",
         "wirecutter@nytimes.com", "cryptosum@mail.beehiiv.com", "kalshi@mail",
         "no-reply@updates.patreon.com", "no-reply@info.patreon.com")

CANON = re.compile(r"https?://[^\s\)\]\"'>]+")


def env_value(name: str) -> str:
    if not ENV.exists():
        return ""
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def log(m: str) -> None:
    print(f"[inbox-review] {m}", flush=True)


def fetch_text(url: str, limit: int = 9000) -> str:
    """Fetch a post and reduce to readable text."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            "Accept-Encoding": "gzip"})
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        h = raw.decode("utf-8", "replace")
    except Exception as e:
        return f"[fetch failed: {str(e)[:90]}]"
    h = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", h)
    t = re.sub(r"(?s)<[^>]+>", " ", h)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
          .replace("&quot;", '"').replace("&#8220;", '"').replace("&#8221;", '"'))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n\n", t).strip()
    # drop the boilerplate head
    for marker in ("SubscribeSign in", "Share", "Thanks for reading"):
        i = t.find(marker)
        if i > 400:
            t = t[i + len(marker):]
            break
    return t[:limit]


def canonical(body: str) -> str:
    for u in CANON.findall(body):
        u = u.rstrip(".,) ")
        if any(d in u for d in ("substack.com/p/", "chinatalk.media/p/", "stratechery.com/20",
                                "newsletter.doomberg.com/p/", "marginalrevolution.com/",
                                "generalist.com/p/", "interconnects.ai/p/")):
            return u
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--max-fetch", type=int, default=12, help="max Substack posts to fetch in full")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    key = env_value("AGENTMAIL_API_KEY")
    if not key:
        log("ERROR: AGENTMAIL_API_KEY missing")
        return 2
    from agentmail import AgentMail

    kw = {"api_key": key}
    client = AgentMail(**kw)
    inbox = client.inboxes.list().inboxes[0].inbox_id
    msgs = client.inboxes.messages.list(inbox, limit=args.limit).messages

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=args.hours)
    items, seen_subj = [], set()
    for m in msgs:
        frm = str(getattr(m, "from_", "") or "")
        if "trevor" in frm.lower():
            continue
        if any(n in frm.lower() for n in NOISE):
            continue
        created = getattr(m, "created_at", "")
        try:
            when = dt.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=dt.timezone.utc)
        except Exception:
            when = None
        if when and when < cutoff:
            continue
        subj = str(getattr(m, "subject", "") or "")
        if subj in seen_subj:
            continue
        seen_subj.add(subj)
        mid = str(getattr(m, "message_id", "") or "")
        prev = re.sub(r"\s+", " ", str(getattr(m, "preview", "") or ""))
        body = ""
        try:
            full = client.inboxes.messages.get(inbox_id=inbox, message_id=mid)
            body = str(getattr(full, "text", "") or "")
            if not body:
                body = re.sub(r"<[^>]+>", " ", str(getattr(full, "html", "") or ""))
            body = re.sub(r"\s+", " ", body).strip()
        except Exception:
            pass
        url = canonical(body) or canonical(prev)
        items.append({
            "date": str(created)[:16], "from": frm, "subject": subj,
            "is_substack": any(s in (frm + url).lower() for s in SUBSTACK_HINTS),
            "url": url, "body": body[:2000], "preview": prev[:400],
        })

    subs = [i for i in items if i["is_substack"] and i["url"]]
    log(f"{len(items)} items in last {args.hours}h; {len(subs)} Substack items with URLs")
    for it in subs[: args.max_fetch]:
        it["full_text"] = fetch_text(it["url"])
        log(f"  fetched {it['subject'][:60]} ({len(it['full_text'])} chars)")

    day = dt.date.today().isoformat()
    TASKS.mkdir(parents=True, exist_ok=True)
    (TASKS / f"inbox-review-{day}.json").write_text(json.dumps(
        {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
         "window_hours": args.hours, "items": items}, indent=1))

    out = [f"# Inbox review — raw material ({day}, last {args.hours}h)", "",
           f"Items: {len(items)} · Substack items: {len(subs)}", ""]
    for it in items:
        out.append(f"## {it['subject']}")
        out.append(f"- from: {it['from']}")
        out.append(f"- date: {it['date']}")
        out.append(f"- substack: {it['is_substack']}")
        if it["url"]:
            out.append(f"- url: {it['url']}")
        body = it.get("full_text") or it["preview"] or it["body"][:600]
        out.append("")
        out.append(body[:6000])
        out.append("")
    (TASKS / f"inbox-review-{day}.md").write_text("\n".join(out))
    log(f"wrote {TASKS / f'inbox-review-{day}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
