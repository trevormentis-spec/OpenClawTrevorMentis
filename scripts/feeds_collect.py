#!/usr/bin/env python3
"""
Daily Inbox Review — feed stage ("subscriptions" that actually work).

Substack blocks automated email subscription (403), so instead of subscribing an inbox we
poll each publication's public RSS feed. Free posts come through in full, no account, no
confirmation email, and nothing is added to the mailbox.

Feeds were selected by cross-recommendation (recommended by 2+ publications we already read)
and filtered for explanatory value — mechanism + strategic depth — over general commentary.

Writes: tasks/feeds-<date>.md  (+ .json)

Usage
    python3 scripts/feeds_collect.py                    # last 24h
    python3 scripts/feeds_collect.py --hours 48
    python3 scripts/feeds_collect.py --status           # just report feed health
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import gzip
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
TASKS = REPO / "tasks"
STATE = REPO / "brain" / "working-memory" / "feeds-seen.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept-Encoding": "gzip"}

# verified 2026-09-23: name -> (feed url, category)
FEEDS = {
    # AI research / strategy
    "Epoch AI": ("https://epochai.substack.com/feed", "ai"),
    "AI as Normal Technology": ("https://www.aisnakeoil.com/feed", "ai"),
    "Ahead of AI (Raschka)": ("https://magazine.sebastianraschka.com/feed", "ai"),
    "Deep (Learning) Focus": ("https://cameronrwolfe.substack.com/feed", "ai"),
    "Latent.Space": ("https://www.latent.space/feed", "ai"),
    "Dwarkesh Podcast": ("https://www.dwarkesh.com/feed", "ai"),
    "Rising Tide (Helen Toner)": ("https://helentoner.substack.com/feed", "ai"),
    # China / geopolitics
    "Paper Tiger (Julian Gewirtz)": ("https://juliangewirtz.substack.com/feed", "china"),
    "Recent Works (Chang Che)": ("https://changche.substack.com/feed", "china"),
    "UnderReported China": ("https://underreportedchina.substack.com/feed", "china"),
    "Peking Hotel": ("https://pekinghotel.substack.com/feed", "china"),
    "kamilkazani": ("https://kamilkazani.substack.com/feed", "china"),
    "Active Faults": ("https://activefaults.substack.com/feed", "china"),
    "Comment is Freed (Sam Freedman)": ("https://samf.substack.com/feed", "policy"),
    # security / economics / industry
    "Chris Miller's Newsletter": ("https://chrismillersnewsletter.substack.com/feed", "industry"),
    "Chips, Guns, and Money": ("https://chipsgunsandmoney.substack.com/feed", "industry"),
    "Conflict (Stephen Roach)": ("https://stephenroach.substack.com/feed", "security"),
    "Mind of Things": ("https://justinmc.substack.com/feed", "security"),
    "Roots of Progress": ("https://rootsofprogress.org/feed", "progress"),
    # mainstream press (added 2026-09-23 at Roderick's request)
    "The Economist": ("https://www.economist.com/latest/rss.xml", "press"),
    "The New Yorker": ("https://www.newyorker.com/feed/everything", "press"),
    "Wired": ("https://www.wired.com/feed/rss", "press"),
    # direct feeds blocked: New Statesman 403, Spectator 404 -> indexed via Google News.
    # Caveat: the Spectator index also returns archive/event/shop pages, so expect noise;
    # its real recent pieces are recoverable by search, not by feed.
    "New Statesman": ("https://news.google.com/rss/search?q=" + urllib.parse.quote("site:newstatesman.com") +
                      "&hl=en-US&gl=US&ceid=US:en", "press"),
    "The Spectator": ("https://news.google.com/rss/search?q=" + urllib.parse.quote("site:spectator.co.uk") +
                      "&hl=en-GB&gl=GB&ceid=GB:en", "press"),
}

# known-dead / stale, recorded so we do not re-test blindly
DEAD = {"culpium": "HTTP 404", "simonwillison": "HTTP 404",
        "valueadded": "stale (last item 2020)"}


def log(m: str) -> None:
    print(f"[feeds] {m}", flush=True)


def fetch(url: str) -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return f"__HTTP_{e.code}__"
    except Exception as e:
        return f"__ERR_{str(e)[:60]}__"


def clean(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s or "")
    s = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
          .replace("&#8220;", '"').replace("&#8221;", '"').replace("&quot;", '"'))
    return re.sub(r"[ \t\xa0]+", " ", s).strip()


def parse(xml: str) -> list[dict]:
    items = []
    for block in re.findall(r"(?is)<item>(.*?)</item>", xml) or \
                 re.findall(r"(?is)<entry>(.*?)</entry>", xml):
        def g(tag):
            m = re.search(rf"(?is)<{tag}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", block)
            return m.group(1).strip() if m else ""
        body = g("content:encoded") or g("description") or g("summary") or g("content")
        items.append({
            "title": clean(g("title")),
            "link": g("link") or (re.search(r'href="([^"]+)"', block) or [None, ""])[1],
            "date": g("pubDate") or g("updated") or g("published"),
            "text": clean(body)[:5000],
        })
    return items


def within(date_str: str, hours: int) -> bool:
    if not date_str:
        return True
    try:
        d = email.utils.parsedate_to_datetime(date_str)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        try:
            d = dt.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return True
    return (dt.datetime.now(dt.timezone.utc) - d) < dt.timedelta(hours=hours)


def load_seen() -> set:
    """Feeds publish weekly, so a time window is the wrong filter. Track which items we have
    already surfaced and report the DELTA — that is what 'new since yesterday' actually means."""
    try:
        return set(json.loads(STATE.read_text()) if STATE.exists() else [])
    except Exception:
        return set()


def save_seen(seen: set) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(sorted(seen)))  # grows slowly; items are URLs
    except Exception as e:
        log(f"state write failed (non-fatal): {e}")


def item_id(i: dict) -> str:
    return (i.get("link") or "") + "|" + (i.get("title") or "")[:80]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24,
                    help="max age for a first-time item (older items are marked seen, not surfaced)")
    ap.add_argument("--bootstrap-days", type=int, default=14,
                    help="on first run, only surface items newer than this")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    seen = load_seen()
    first_run = not seen
    max_age = (args.bootstrap_days * 24) if first_run else args.hours

    results, health = [], []
    for name, (url, cat) in FEEDS.items():
        xml = fetch(url)
        if xml.startswith("__"):
            health.append((name, xml.strip("_")))
            log(f"  FAIL {name:34s} {xml.strip('_')}")
            continue
        items = parse(xml)
        new = []
        for i in items:
            iid = item_id(i)
            if iid in seen:
                continue
            seen.add(iid)                      # seen either way; old posts must not flood
            if within(i["date"], max_age):
                new.append(i)
        health.append((name, f"ok ({len(new)} new)"))
        log(f"  ok   {name:34s} {len(new)} new")
        for i in new:
            i["feed"] = name
            i["category"] = cat
            results.append(i)

    save_seen(seen)

    if args.status:
        print("\nfeed health:")
        for n, s in health:
            print(f"  {n:34s} {s}")
        print("\nknown dead:", DEAD)
        return 0

    day = dt.date.today().isoformat()
    TASKS.mkdir(parents=True, exist_ok=True)
    (TASKS / f"feeds-{day}.json").write_text(json.dumps(
        {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
         "hours": args.hours, "feeds_total": len(FEEDS), "items": results,
         "feed_health": [{"feed": n, "status": s} for n, s in health]}, indent=1))

    out = [f"# Substack feed material ({day}, seen-ledger delta)", "",
           f"Feeds polled: {len(FEEDS)} · new items: {len(results)} · "
           f"first_run={first_run} (max age {max_age}h)", ""]
    for i in results:
        out += [f"## [{i['feed']}] {i['title']}", f"- url: {i['link']}",
                f"- date: {i['date']}", "", i["text"][:4500], ""]
    (TASKS / f"feeds-{day}.md").write_text("\n".join(out))
    log(f"{len(results)} items from {len(FEEDS)} feeds -> {TASKS / f'feeds-{day}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
