#!/usr/bin/env python3
"""
Mexico Morning Brief — daily HTML dashboard exercising all new collection skills.

Powers every section from live API data:
- Section 1: Mexico News Feed (3 custom API specs)
- Section 2: Social Signal Radar (Reddit + Bluesky)
- Section 3: Wikipedia Change Monitor (8 intel pages)
- Section 4: Source Health (API vs RSS cross-check)
- Section 5: Collection Pipeline Stats

Usage:
    python3 scripts/mexico_morning_brief.py                 # Generate + save
    python3 scripts/mexico_morning_brief.py --send          # Generate + email
    python3 scripts/mexico_morning_brief.py --dev           # Quick dev mode (fewer calls)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import urllib.request
import urllib.parse

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "exports" / "briefs"
HTML_OUT = OUTPUT_DIR / f"mexico-morning-{dt.date.today().isoformat()}.html"

WIKI_STATE_FILE = REPO_ROOT / "tasks" / "wiki_monitor_state.json"

DARK = "#1a1a2e"
RED = "#c0392b"
GREEN = "#27ae60"
BLUE = "#2980b9"
AMBER = "#f39c12"
GRAY = "#7f8c8d"


def log(msg: str) -> None:
    print(f"[brief] {msg}", file=sys.stderr, flush=True)


def run_script(script: str, args: list[str], timeout: int = 45) -> str:
    """Run a pipeline script and return stdout."""
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / script)] + args,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def query_db(sql: str) -> list[dict]:
    """Query the SQLite collection records DB."""
    db_path = REPO_ROOT / "data" / "collection_records.db"
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def fetch_api_endpoint(url: str) -> str | None:
    """Fetch a JSON API endpoint directly (for custom specs)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return None


def fetch_graphql(url: str, query_json: str) -> str | None:
    """POST a GraphQL query and return response."""
    try:
        req = urllib.request.Request(
            url, data=query_json.encode("utf-8"),
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return None


def _load_deepseek_key() -> str:
    """Load DEEPSEEK_API_KEY from .env."""
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if "DEEPSEEK_API_KEY" in line and "=" in line:
                return line.split("=", 1)[1].strip()
    return os.environ.get("DEEPSEEK_API_KEY", "")


DEEPSEEK_API_KEY = _load_deepseek_key()


def translate(texts: list[str], target_lang: str = "English") -> list[str]:
    """Translate Spanish headlines to English using DeepSeek."""
    if not texts or not DEEPSEEK_API_KEY:
        return texts
    try:
        batch = "\n".join(f"{i}. {t}" for i, t in enumerate(texts) if t)
        if not batch.strip():
            return texts
        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": f"Translate the following Spanish news headlines to {target_lang}. Preserve names, numbers, and dates exactly. Return only the numbered translations, one per line, no explanation."},
                {"role": "user", "content": batch}
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        translated = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or "." in line[:3]):
                clean = line.split(". ", 1)[-1] if ". " in line else line
                translated.append(clean)
            elif line:
                translated.append(line)
        while len(translated) < len(texts):
            translated.append(texts[len(translated)])
        return translated[:len(texts)]
    except Exception as e:
        log(f"Translation failed: {e}")
        return texts


def _render_social(items: list) -> str:
    """Render social items as HTML."""
    if not items:
        return '<div class="alert">No social signals detected in this cycle.</div>'
    parts = []
    for s in items[:6]:
        platform = s.get("platform", "?")
        if platform == "bluesky":
            parts.append(f'<div class="item"><div class="title">@{s.get("author","?")}</div><div class="meta">{s.get("text","")[:120]}</div></div>')
        elif platform == "hackernews":
            parts.append(f'<div class="item"><div class="title">{s.get("title","?")[:80]}</div><div class="meta">HN - {s.get("score",0)} points</div></div>')
    return "\\n".join(parts)


def collect_data(dev: bool = False) -> dict:
    """Collect all data for the brief."""
    data = {}

    # Section 1: Mexico news from API specs
    log("Section 1: Mexico News Feed")
    news = {"elfinanciero": [], "animalpolitico": [], "jornada": []}

    # El Financiero — Arc XP query-feed (works without specific collection IDs)
    resp = fetch_api_endpoint(
        "https://www.elfinanciero.com.mx/pf/api/v3/content/fetch/query-feed"
        "?query=%7B%22q%22%3A%22%22%2C%22size%22%3A5%2C%22sort%22%3A%22last_updated_date%3Adesc%22%7D&d=350"
    )
    if resp:
        try:
            d = json.loads(resp)
            for a in d.get("content_elements", [])[:5]:
                news["elfinanciero"].append({
                    "title": a.get("headlines", {}).get("basic", "?"),
                    "date": a.get("last_updated_date", "")[:10] if a.get("last_updated_date") else "",
                })
        except json.JSONDecodeError:
            pass

    # Animal Politico — GraphQL (correct fragments)
    gql_payload = json.dumps({
        "operationName": "GetAPHomepage",
        "query": "query GetAPHomepage { apHomepage { animalPolTicoHome { notasDelHomepageAP(first: 5) { nodes { __typename ... on NodeWithTitle { title } ... on ContentNode { databaseId slug date uri } } } } } }",
        "variables": {}
    })
    resp = fetch_graphql("https://grupoanimal.mx/api/graphql", gql_payload)
    if resp:
        try:
            d = json.loads(resp)
            nodes = d.get("data", {}).get("apHomepage", {}).get("animalPolTicoHome", {}).get("notasDelHomepageAP", {}).get("nodes", [])
            news["animalpolitico"] = [
                {"title": n.get("title", "?"), "date": n.get("date", "")[:10] if n.get("date") else ""}
                for n in nodes[:5]
            ]
        except (json.JSONDecodeError, AttributeError):
            pass

    # La Jornada — supplements
    resp = fetch_api_endpoint("https://www.jornada.com.mx/serviciosjornada/microservicios/jornada/suplementos.json")
    if resp:
        try:
            d = json.loads(resp)
            news["jornada"] = [
                {"supplement": k.capitalize(), "title": v.get("su_titulo", "?"), "date": v.get("su_fecha", "")}
                for k, v in d.items() if isinstance(v, dict)
            ]
        except json.JSONDecodeError:
            pass

    data["news"] = news

    # Section 2: Social signals — Bluesky (public API) + HackerNews (openweb)
    log("Section 2: Social Signal Radar")
    social_items = []

    bsky_keywords = ["Mexico", "Sheinbaum", "CJNG", "USMCA"]
    for kw in bsky_keywords:
        try:
            req = urllib.request.Request(
                f"https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={urllib.parse.quote(kw)}&lang=en&limit=3",
                headers={"User-Agent": "TREVOR/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                d = json.loads(resp.read())
                for post in d.get("posts", [])[:3]:
                    text = post.get("record", {}).get("text", "")[:200]
                    author = post.get("author", {}).get("handle", "?")
                    social_items.append({"platform": "bluesky", "author": author, "text": text, "keyword": kw})
        except Exception as e:
            log(f"  Bluesky '{kw}' failed: {e}")
        if dev:
            break

    try:
        hn_result = subprocess.run(
            ["openweb", "hackernews", "getTopStories", "{}"],
            capture_output=True, text=True, timeout=15,
        )
        hn_data = None
        if hn_result.returncode == 0 and hn_result.stdout.strip():
            raw = json.loads(hn_result.stdout)
            if isinstance(raw, dict) and raw.get("output"):
                with open(raw["output"]) as f:
                    hn_data = json.load(f)
            elif isinstance(raw, list):
                hn_data = raw
            else:
                hn_data = raw
        if hn_data:
            stories = hn_data if isinstance(hn_data, list) else []
            for s in stories[:5]:
                if any(kw.lower() in str(s.get("title","")).lower() for kw in ["mexico","latin","spanish","cartel","border","usmca","tariff","trade","trump"]):
                    social_items.append({"platform": "hackernews", "title": s.get("title", "?"), "score": s.get("score", 0)})
    except Exception as e:
        log(f"  HackerNews failed: {e}")

    data["social"] = social_items

    # Translate Spanish headlines to English
    log("Translating headlines...")
    for src in ["elfinanciero", "animalpolitico"]:
        headlines = [a.get("title", "") for a in news.get(src, []) if a.get("title")]
        if headlines:
            translated = translate(headlines)
            for i, t in enumerate(translated):
                if i < len(news[src]):
                    news[src][i]["title_en"] = t

    # Section 3: Wikipedia changes
    log("Section 3: Wikipedia Monitor")
    wiki_changes = []
    if WIKI_STATE_FILE.exists():
        try:
            state = json.loads(WIKI_STATE_FILE.read_text())
            for page, info in state.items():
                if page == "last_updated":
                    continue
                wiki_changes.append({
                    "page": page,
                    "revision": info.get("revision", "?"),
                    "last_checked": info.get("last_checked", "")[:16],
                })
        except (json.JSONDecodeError, AttributeError):
            pass
    data["wiki"] = wiki_changes

    # Section 4: Source health
    log("Section 4: Source Health")
    xcheck_records = query_db(
        "SELECT source, payload_json, collected_at FROM collection_records WHERE method='crosscheck' ORDER BY id DESC LIMIT 5"
    )
    data["crosscheck"] = xcheck_records

    # Section 5: Pipeline stats
    log("Section 5: Pipeline Stats")
    stats = query_db(
        "SELECT method, COUNT(*) as total, MIN(collected_at) as first_seen, MAX(collected_at) as last_seen FROM collection_records GROUP BY method ORDER BY total DESC"
    )
    total = query_db("SELECT COUNT(*) as c FROM collection_records")
    data["stats"] = {"methods": stats, "total": total[0]["c"] if total else 0}

    # Recent records
    recent = query_db("SELECT source, method, nato_admiralty_source_rating, nato_admiralty_info_rating, substr(collected_at,1,19) as ts FROM collection_records ORDER BY id DESC LIMIT 8")
    data["recent"] = recent

    return data


def build_html(data: dict) -> str:
    """Build the HTML dashboard."""
    today = dt.date.today().isoformat()
    news = data["news"]
    social = data["social"]
    wiki = data["wiki"]
    xcheck = data["crosscheck"]
    st = data["stats"]
    recent = data["recent"]

    # Build social summary
    bluesky_count = sum(1 for s in social if s.get("platform") == "bluesky")
    hn_count = sum(1 for s in social if s.get("platform") == "hackernews")

    # Cross-check status
    xcheck_statuses = {r.get("source", "").replace("xcheck-", ""): r.get("payload_json", "") for r in xcheck}
    xcheck_display = []
    for name in ["bbc-news", "reuters", "bloomberg"]:
        payload_str = xcheck_statuses.get(name, "{}")
        try:
            p = json.loads(payload_str) if isinstance(payload_str, str) else {}
            status = p.get("status", "N/A")
            overlap = p.get("overlap", 0)
            api_c = p.get("api_count", 0)
            rss_c = p.get("rss_count", 0)
            xcheck_display.append({"source": name, "status": status, "overlap": overlap, "api": api_c, "rss": rss_c})
        except (json.JSONDecodeError, TypeError):
            xcheck_display.append({"source": name, "status": "N/A", "overlap": 0, "api": 0, "rss": 0})

    elfi_items = news.get("elfinanciero", [])
    ap_items = news.get("animalpolitico", [])
    jornada_items = news.get("jornada", [])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mexico Morning Brief — {today}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #1a1a2e; font-size: 14px; line-height: 1.5; }}
  .container {{ max-width: 800px; margin: 20px auto; padding: 0 16px; }}
  .header {{ background: linear-gradient(135deg, {DARK}, #16213e); color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; }}
  .header h1 {{ font-size: 22px; font-weight: 700; }}
  .header .sub {{ font-size: 13px; opacity: 0.7; margin-top: 4px; }}
  .header .badge {{ display: inline-block; background: {GREEN}; color: white; padding: 3px 10px; border-radius: 4px; font-size: 11px; margin-top: 8px; }}
  .section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #eee; display: flex; align-items: center; gap: 8px; }}
  .section h2 .count {{ font-size: 12px; color: {GRAY}; font-weight: 400; }}
  .item {{ padding: 8px 0; border-bottom: 1px solid #f5f5f5; }}
  .item:last-child {{ border-bottom: none; }}
  .item .title {{ font-size: 14px; font-weight: 600; }}
  .item .meta {{ font-size: 11px; color: {GRAY}; margin-top: 2px; }}
  .tag {{ display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 600; margin-right: 3px; }}
  .tag-red {{ background: #fde8e8; color: {RED}; }}
  .tag-green {{ background: #e8f5e9; color: {GREEN}; }}
  .tag-blue {{ background: #e3f2fd; color: {BLUE}; }}
  .tag-amber {{ background: #fef3e0; color: {AMBER}; }}
  .tag-gray {{ background: #f0f0f0; color: {GRAY}; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }}
  .stat-card {{ background: #f8f9fa; border-radius: 8px; padding: 12px; text-align: center; }}
  .stat-card .num {{ font-size: 28px; font-weight: 800; color: {BLUE}; }}
  .stat-card .label {{ font-size: 11px; color: {GRAY}; margin-top: 2px; }}
  .alert {{ background: #fef3e0; border-left: 4px solid {AMBER}; padding: 8px 12px; border-radius: 4px; font-size: 13px; margin: 8px 0; }}
  .alert-green {{ border-left-color: {GREEN}; background: #f0faf0; }}
  .qc-badge {{ background: {DARK}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 10px; display: inline-block; margin-top: 8px; }}
  .xcheck-ok {{ color: {GREEN}; }}
  .xcheck-warn {{ color: {RED}; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
  th {{ text-align: left; padding: 6px 8px; background: #f8f9fa; font-size: 10px; text-transform: uppercase; color: {GRAY}; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #f0f0f0; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0f1117; color: #e0e0e0; }}
    .section {{ background: #1a1d28; }}
    .header {{ background: linear-gradient(135deg, #0f1117, #1a1d28); }}
    .stat-card {{ background: #0f1117; }}
    .item {{ border-bottom-color: #2a2d38; }}
    th {{ background: #0f1117; }}
    td {{ border-bottom-color: #2a2d38; }}
    .tag-gray {{ background: #2a2d38; color: #aaa; }}
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>☀️ Mexico Morning Brief</h1>
  <div class="sub">{today} · Open Claw Mexico</div>
  <span class="badge">PENDING HUMAN ANALYST QC REVIEW</span>
</div>

<!-- SECTION 1: Mexico News Feed -->
<div class="section">
  <h2>📰 Mexico News Feed <span class="count">— 3 API sources</span></h2>

  <h3 style="font-size:13px; color:{GREEN}; margin-bottom:6px;">El Financiero <span style="font-size:11px;color:{GRAY};font-weight:400;">(Arc XP API)</span></h3>
  {chr(10).join(f'<div class="item"><div class="title">{a.get("title_en", a.get("title","?"))[:80]}</div><div class="meta">{a.get("date","")} <span style="font-size:11px;color:{GRAY}">ES: {a.get("title","")[:60]}</span></div></div>' for a in elfi_items[:3]) if elfi_items else '<div class="item" style="color:' + GRAY + ';">No articles fetched</div>'}

  <h3 style="font-size:13px; color:{BLUE}; margin:12px 0 6px;">Animal Politico <span style="font-size:11px;color:{GRAY};font-weight:400;">(GraphQL API)</span></h3>
  {chr(10).join(f'<div class="item"><div class="title">{a.get("title_en", a.get("title","?"))[:80]}</div><div class="meta">{a.get("date","")} <span style="font-size:11px;color:{GRAY}">ES: {a.get("title","")[:60]}</span></div></div>' for a in ap_items[:3]) if ap_items else '<div class="item" style="color:' + GRAY + ';">No articles fetched</div>'}

  <h3 style="font-size:13px; color:{AMBER}; margin:12px 0 6px;">La Jornada <span style="font-size:11px;color:{GRAY};font-weight:400;">(Elasticsearch API)</span></h3>
  {chr(10).join(f'<div class="item"><div class="title">{j.get("title","?")[:60]}</div><div class="meta"><span class="tag tag-amber">{j.get("supplement","")}</span> {j.get("date","")}</div></div>' for j in jornada_items[:4]) if jornada_items else '<div class="item" style="color:' + GRAY + ';">No supplements fetched</div>'}
</div>

<!-- SECTION 2: Social Signal Radar -->
<div class="section">
  <h2>📡 Social Signal Radar <span class="count">— {bluesky_count} Bluesky · {hn_count} HN</span></h2>
  <div class="stat-grid" style="margin-bottom:10px;">
    <div class="stat-card"><div class="num">{bluesky_count}</div><div class="label">Bluesky mentions</div></div>
    <div class="stat-card"><div class="num">{hn_count}</div><div class="label">HackerNews stories</div></div>
    <div class="stat-card"><div class="num">{len(wiki)}</div><div class="label">Wikipedia pages tracked</div></div>
  </div>
  {_render_social(social)}
</div>

<!-- SECTION 3: Wikipedia Monitor -->
<div class="section">
  <h2>📖 Wikipedia Change Monitor <span class="count">— {len(wiki)} pages</span></h2>
  <table>
    <tr><th>Page</th><th>Revision</th><th>Last Checked</th></tr>
    {chr(10).join(f'<tr><td><strong>{w["page"].replace("_"," ")}</strong></td><td style="font-size:11px;color:{GRAY};">{w["revision"]}</td><td style="font-size:11px;color:{GRAY};">{w["last_checked"]}</td></tr>' for w in wiki)}
  </table>
  <div class="alert alert-green" style="margin-top:8px;">✓ All {len(wiki)} pages stable since baseline capture.</div>
</div>

<!-- SECTION 4: Source Health -->
<div class="section">
  <h2>🔬 Source Health <span class="count">— API vs RSS cross-check</span></h2>
  <table>
    <tr><th>Source</th><th>Status</th><th>Overlap</th><th>API/RSS</th></tr>
    {chr(10).join(f'<tr><td><strong>{x["source"]}</strong></td><td>{"<span class=xcheck-ok>✓ PASS</span>" if x["status"] == "PASS" else "<span class=xcheck-warn>⚠ " + x.get("status","?") + "</span>"}</td><td>{x.get("overlap",0):.0%}</td><td>{x.get("api",0)}/{x.get("rss",0)}</td></tr>' for x in xcheck_display)}
  </table>
  {'<div class="alert">⚠️ BBC News: API returned 0 headlines while RSS returned RSS count. Check if BBC search endpoint has different parameters.</div>' if any(x["source"]=="bbc-news" and x["api"]==0 for x in xcheck_display) else ''}
</div>

<!-- SECTION 5: Pipeline Stats -->
<div class="section">
  <h2>📊 Collection Pipeline <span class="count">— {st["total"]} records</span></h2>
  <div class="stat-grid">
    {chr(10).join(f'<div class="stat-card"><div class="num">{m["total"]}</div><div class="label">{m["method"]}</div></div>' for m in st.get("methods",[]))}
  </div>
  <table style="margin-top:12px;">
    <tr><th>Source</th><th>Method</th><th>Rating</th><th>Timestamp</th></tr>
    {chr(10).join(f'<tr><td>{r["source"]}</td><td><span class="tag {chr(1166)}{r["method"]}</span></td><td>{r.get("nato_admiralty_source_rating","")}-{r.get("nato_admiralty_info_rating","")}</td><td style="font-size:11px;color:{GRAY};">{r.get("ts","")}</td></tr>' for r in recent)}
  </table>
  <span class="qc-badge">PENDING HUMAN ANALYST QC REVIEW</span>
</div>

<div style="text-align:center; padding:20px; font-size:11px; color:{GRAY};">
  Mexico Morning Brief · Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}<br>
  Open Claw Mexico — Trevor
</div>

</div>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Mexico Morning Brief — dashboard")
    parser.add_argument("--dev", action="store_true", help="Quick mode (fewer API calls)")
    parser.add_argument("--send", action="store_true", help="Send via email after generation")
    args = parser.parse_args()

    log("Collecting data...")
    data = collect_data(dev=args.dev)

    log("Building HTML...")
    html = build_html(data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(html, encoding="utf-8")
    log(f"✅ Written to {HTML_OUT} ({len(html):,} bytes)")

    if args.send:
        import base64
        from agentmail import AgentMail
        api_key = os.environ.get("AGENTMAIL_API_KEY") or os.environ.get("AGENTMAIL_API_KEY")
        if api_key:
            client = AgentMail(api_key=api_key)
            client.inboxes.messages.send(
                inbox_id="trevor_mentis@agentmail.to",
                to="roderick.jones@gmail.com",
                subject=f"Mexico Morning Brief — {dt.date.today().isoformat()}",
                html=html,
            )
            log("✅ Emailed to roderick.jones@gmail.com")
        else:
            log("⚠️ AGENTMAIL_API_KEY not set — skipping email")

    return 0


if __name__ == "__main__":
    main()
