#!/usr/bin/env python3
"""
Moltbook collection — read-only threat-intel sweep (Operation: Agent Ecosystem Collection).

READ-ONLY. Never posts, never changes account state, never installs or executes anything
found in the data. Every fetched byte is treated as DATA, not instructions.

Pulls recent posts across target submolts and scans for the six priority categories:
  1 prompt-injection / manipulation      4 owner leakage (PATTERN level only)
  2 malicious skills / tool promotion    5 coordinated activity (duplicate/near-dup clusters)
  3 impersonation                        6 agent-to-agent commerce / fraud

Outputs (all under tmp/moltbook-<date>/):
  raw_posts.json        everything fetched, verbatim
  candidates.jsonl      scored hits with category + matched evidence
  scan_summary.json     counts by category and submolt

Usage: python3 scripts/moltbook_collect.py [--limit 400] [--submolts security,agents,ai]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CREDS = pathlib.Path.home() / ".config" / "moltbook" / "credentials.json"
UA = {"User-Agent": "Trevor-ThreatIntel trevor_mentis@agentmail.to", "Accept": "application/json"}
BASE = "https://www.moltbook.com/api/v1"

# --- category pattern banks (deliberately conservative; we want signal not noise) ---
P = {
    "prompt_injection": [
        r"ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instruction|prompt|rule)",
        r"disregard\s+(your\s+|all\s+)?(instruction|rule|guideline|system)",
        r"you\s+are\s+now\s+(a|an|the)\b",
        r"new\s+instructions?\s*:",
        r"(reveal|print|show|output|leak)\s+(me\s+)?(your\s+)?(system\s+prompt|instruction|config|api\s*key|token|credential)",
        r"do\s+not\s+(tell|inform|notify)\s+(your\s+)?(owner|human|user|principal)",
        r"(send|forward|post|upload|exfiltrate)\s+(me\s+)?(the\s+)?(key|token|credential|password|file|data)",
        r"base64|rot13|\\u200b|\\u200c|\\u200d|zero[- ]width",
        r"when\s+you\s+read\s+this.{0,40}(do|execute|run|call)",
        r"execute\s+(this|the\s+following)\s+(code|command|tool)",
    ],
    "malicious_skill": [
        r"(install|add|enable|load)\s+(this\s+|the\s+)?(skill|plugin|extension|tool|mcp)",
        r"(new|powerful|best)\s+(skill|plugin|tool).{0,60}(free|no\s+auth|open)",
        r"clawhub|skill\.md|SKILLS\.md",
        r"run\s+(this|the\s+following)\s+(script|installer|command)",
        r"copy\s+paste\s+(this|these)\s+(into|to)\s+your",
    ],
    "impersonation": [
        r"i\s+(am|represent|work\s+for)\s+[A-Z][A-Za-z]+(\s+[A-Z][A-Za-z]+)?\s*(from|at|of)?\s*(OpenAI|Anthropic|Google|Microsoft|Meta|Apple|Amazon|Coinbase|Stripe|the\s+team)",
        r"official\s+(account|channel|announcement|team)",
        r"on\s+behalf\s+of\s+(the\s+)?[A-Z][A-Za-z]+",
        r"this\s+is\s+the\s+(real|official)\b",
    ],
    "owner_leakage": [
        r"my\s+(owner|human|principal|operator)\b.{0,80}\b(name|lives|located|works\s+at|salary|net\s+worth|bank|address)",
        r"(we|he|she|they)\s+(live|lives)\s+in\s+[A-Z][a-z]+",
        r"my\s+owner('s)?\s+(travel|trip|flight|itinerary|schedule|calendar)",
        r"(company|employer)\s+(is|:)\s+[A-Z][A-Za-z]+.{0,30}(client|secret|internal)",
    ],
    "commerce_fraud": [
        r"(send|pay|wire|transfer)\s+.{0,30}(btc|eth|usdc|sol|0x[a-fA-F0-9]{6,}|wallet)",
        r"guaranteed\s+(return|profit|yield|apy)",
        r"(escrow|invoice|deposit)\s+(required|first|now|before)",
        r"double\s+your\s+(money|crypto|balance)",
        r"(fake|scam|rug\s*pull)\s+(service|token|coin)",
    ],
}
R = {k: [re.compile(p, re.I) for p in v] for k, v in P.items()}


def log(m: str) -> None:
    print(f"[moltbook] {m}", flush=True)


def api_key() -> str:
    if CREDS.exists():
        try:
            return json.loads(CREDS.read_text())["api_key"]
        except Exception:
            pass
    for line in (REPO / ".env").read_text().splitlines():
        if line.strip().startswith("MOLTBOOK_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


KEY = api_key()


def get(path: str, params: dict | None = None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={**UA, "Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"__error__": str(e)[:120]}


def text_of(p: dict) -> str:
    parts = [str(p.get(k, "") or "") for k in ("title", "body", "content", "text", "description")]
    return " \n ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=600, help="max posts per submolt")
    ap.add_argument("--page", type=int, default=50)
    ap.add_argument("--submolts", default="security,agents,agentfinance,agentskills,builds,tooling,"
                                         "agenteconomy,openclaw-explorers,openclaw,infrastructure,memory,ai")
    args = ap.parse_args()

    day = dt.date.today().isoformat()
    out = REPO / "tmp" / f"moltbook-{day}"
    out.mkdir(parents=True, exist_ok=True)

    log("stats ...")
    stats = get("/stats")
    (out / "stats.json").write_text(json.dumps(stats, indent=1)[:20000])
    log(f"stats: {str(stats)[:200]}")

    # Cursor pagination (the API returns next_cursor; offset is ignored). Target the
    # security-relevant submolts rather than the global firehose.
    posts, seen = [], set()
    targets = [s.strip() for s in args.submolts.split(",") if s.strip()]
    for sm in targets:
        cursor, got = None, 0
        while got < args.limit:
            params = {"limit": args.page, "sort": "new", "submolt": sm}
            if cursor:
                params["cursor"] = cursor
            d = get("/posts", params)
            if isinstance(d, dict) and "__error__" in d:
                log(f"  {sm}: error {d['__error__']}")
                break
            batch = d.get("posts") if isinstance(d, dict) else (d if isinstance(d, list) else [])
            if not batch:
                break
            for p in batch:
                pid = str(p.get("id") or hashlib.md5(text_of(p).encode()).hexdigest()[:12])
                if pid in seen:
                    continue
                seen.add(pid)
                p["_submolt"] = sm
                posts.append(p)
                got += 1
            cursor = d.get("next_cursor") if isinstance(d, dict) else None
            if not cursor or len(batch) < args.page:
                break
        log(f"  r/{sm}: {got} posts (running total {len(posts)})")

    (out / "raw_posts.json").write_text(json.dumps(posts, indent=1))
    log(f"raw posts: {len(posts)} -> {out/'raw_posts.json'}")

    # scan
    hits, by_cat = [], collections.Counter()
    shingles = collections.defaultdict(list)
    for p in posts:
        t = text_of(p)
        low = t.lower()
        author = str(p.get("author") or p.get("agent") or p.get("agent_name") or "?")
        for cat, pats in R.items():
            for rx in pats:
                m = rx.search(t)
                if m:
                    hits.append({
                        "category": cat, "author": author,
                        "submolt": p.get("submolt") or p.get("_submolt") or p.get("community"),
                        "post_id": p.get("id") or p.get("post_id"),
                        "matched": m.group(0)[:160],
                        "excerpt": re.sub(r"\s+", " ", t[max(0, m.start() - 160):m.end() + 160])[:420],
                        "url": f"https://www.moltbook.com/p/{p.get('id') or ''}",
                    })
                    by_cat[cat] += 1
                    break
        # coordination: 8-word shingle fingerprint
        words = re.findall(r"[a-z0-9]+", low)
        for i in range(0, max(0, len(words) - 8)):
            g = " ".join(words[i:i + 8])
            shingles[g].append(author)

    with (out / "candidates.jsonl").open("w") as fh:
        for h in hits:
            fh.write(json.dumps(h) + "\n")

    clusters = {g: sorted(set(a)) for g, a in shingles.items()
                if len(set(a)) >= 4 and len(a) >= 4}
    top_clusters = sorted(clusters.items(), key=lambda kv: -len(kv[1]))[:15]
    (out / "coordination_clusters.json").write_text(json.dumps(
        [{"shingle": g, "agents": a} for g, a in top_clusters], indent=1))

    summary = {"date": day, "posts_scanned": len(posts), "hits": dict(by_cat),
               "total_hits": len(hits), "coordination_clusters": len(clusters),
               "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    (out / "scan_summary.json").write_text(json.dumps(summary, indent=1))
    log(f"scan: {json.dumps(summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
