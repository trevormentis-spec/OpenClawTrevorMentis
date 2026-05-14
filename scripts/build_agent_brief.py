#!/usr/bin/env python3
"""
build_agent_brief.py — Agent-first GSIB product.

Reads analysis JSON files and produces a clean structured JSON brief
designed for AI agent consumption. No PDF, no maps, no visual rendering.
Published to Moltbook + API endpoint.

Usage:
    python3 build_agent_brief.py --working-dir ~/trevor-briefings/2026-05-11
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import os
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
EXPORTS = REPO / "exports" / "agent-api"

REGION_LABELS = {
    "europe": "Europe", "asia": "Asia & Indo-Pacific",
    "middle_east": "Middle East", "north_america": "North America",
    "south_central_america": "South & Central America",
    "global_finance": "Global Finance",
}
REGION_CODE = {
    "europe": "EUR", "asia": "ASP", "middle_east": "MEA",
    "north_america": "NAM", "south_central_america": "SCA",
    "global_finance": "GLF",
}
CONFIDENCE_BANDS = {
    "almost certain": {"lower": 93, "upper": 100, "label": "Almost Certain"},
    "highly likely": {"lower": 80, "upper": 92, "label": "Highly Likely"},
    "likely": {"lower": 60, "upper": 79, "label": "Likely"},
    "roughly even odds": {"lower": 40, "upper": 59, "label": "Roughly Even"},
    "even chance": {"lower": 40, "upper": 59, "label": "Even Chance"},
    "unlikely": {"lower": 20, "upper": 39, "label": "Unlikely"},
    "very unlikely": {"lower": 5, "upper": 19, "label": "Very Unlikely"},
    "almost no chance": {"lower": 0, "upper": 4, "label": "Almost No Chance"},
}

def log(m):
    print(f"[brief] {m}", file=sys.stderr)


def load_analysis(wd, region):
    """Load a theatre analysis JSON."""
    p = wd / "analysis" / f"{region}.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except:
            return {}
    return {}


def load_kalshi(wd):
    """Load Kalshi market data from exports."""
    date_str = dt.date.today().strftime("%Y-%m-%d")
    p = REPO / "exports" / f"kalshi-scan-{date_str}.md"
    if not p.exists():
        return []
    trades = []
    for line in p.read_text().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 8 and parts[0].startswith("KX"):
            try:
                yes_bid = float(parts[1].replace("$", ""))
                volume = int(float(parts[6].replace(",", "")))
                expiry = parts[7] if len(parts) > 7 else ""
                trades.append({
                    "ticker": parts[0],
                    "yes_bid": yes_bid,
                    "yes_ask": float(parts[2].replace("$", "")),
                    "volume": volume,
                    "expiry": expiry,
                    "mid_price": round((yes_bid + float(parts[2].replace("$", ""))) / 2, 2),
                })
            except:
                pass
    return sorted(trades, key=lambda x: x["volume"], reverse=True)[:10]


def build(wd):
    """Build the agent-optimized brief."""
    today = dt.date.today()
    date_str = today.strftime("%Y-%m-%d")
    brief_id = f"gsib-agent-{date_str}"

    brief = {
        "schema": "https://trevormentis.spec/agent-brief/v1",
        "brief_id": brief_id,
        "published": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "OPEN SOURCE — PUBLIC DISTRIBUTION",
        "ttl_hours": 24,
        "prev_brief_id": None,
        "theatre_count": 6,
        "methodology": {
            "framework": "Sherman Kent estimative tradecraft",
            "source_grading": "Modified Admiralty System (A1–F6)",
            "single_source_cap": "likely (70%)",
            "sources": ["ISW", "Reuters", "AP", "BBC", "Al Jazeera", "Crisis Group",
                       "Carnegie Endowment", "Chatham House", "IAEA", "ACLED",
                       "Polymarket", "Kalshi"],
            "models": ["DeepSeek V4 Pro", "Claude Opus 4.7"],
        },
        "cross_cutting_analysis": {},
        "theatres": [],
        "prediction_markets": [],
        "watch_items": [],
        "indicators": {},
    }

    # Load executive summary
    exec_data = load_analysis(wd, "exec_summary")
    if exec_data:
        brief["cross_cutting_analysis"] = {
            "bluf": exec_data.get("bluf", ""),
            "context": exec_data.get("context", exec_data.get("narrative", "")),
            "overall_assessment": exec_data.get("overall_assessment", ""),
        }

    # Build key judgments cross-cut
    all_kjs = []

    # Process each theatre
    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]

    for region in regions:
        data = load_analysis(wd, region)
        if not data:
            continue

        subtitle = {
            "europe": "Truce & Strategic Dynamics",
            "asia": "Diplomacy & Power Projection",
            "middle_east": "Framework & Kinetic Cycle",
            "north_america": "Coordination & Sovereignty",
            "south_central_america": "Political & Financial Pressures",
            "global_finance": "Risk & Liquidity Conditions",
        }.get(region, "Overview")

        theatre = {
            "region": region,
            "region_code": REGION_CODE.get(region, region.upper()[:3]),
            "region_label": REGION_LABELS.get(region, region.replace("_", " ").title()),
            "section_title": subtitle,
            "narrative": data.get("narrative", ""),
            "story": data.get("story", ""),
            "key_judgments": [],
            "indicators": data.get("indicators", data.get("by_the_numbers", [])),
            "incident_count": data.get("incident_count", 0),
        }

        # Key judgments
        for i, kj in enumerate(data.get("key_judgments", [])):
            band_str = kj.get("sherman_kent_band", "").lower().strip()
            band_info = CONFIDENCE_BANDS.get(band_str, {"lower": 0, "upper": 100, "label": band_str.title()})
            kj_entry = {
                "id": f"KJ-{REGION_CODE.get(region, 'XX')}-{i+1}",
                "statement": kj.get("statement", ""),
                "confidence_band": band_info["label"],
                "probability_lower": band_info["lower"],
                "probability_upper": band_info["upper"],
                "prediction_pct": kj.get("prediction_pct", 0),
                "confidence_in_judgment": kj.get("confidence_in_judgment", ""),
                "horizon_days": 7,
                "falsification": kj.get("what_would_change", ""),
                "source_grading_note": kj.get("source_grading_note", ""),
            }
            theatre["key_judgments"].append(kj_entry)
            all_kjs.append({
                "id": kj_entry["id"],
                "region": region,
                "statement": kj_entry["statement"],
                "band": band_info["label"],
                "probability": f"{band_info['lower']}-{band_info['upper']}%",
                "horizon": "7 days",
            })

        brief["theatres"].append(theatre)

    # Cross-cutting key judgments
    brief["cross_cutting_analysis"]["key_judgments"] = all_kjs

    # Executive summary key judgments (from the exec summary file)
    if exec_data:
        exec_kjs = exec_data.get("five_judgments", [])
        brief["cross_cutting_analysis"]["summary_judgments"] = [
            {
                "region": kj.get("drawn_from_region", "global"),
                "statement": kj.get("statement", ""),
                "band": kj.get("sherman_kent_band", ""),
                "probability": f"{kj.get('prediction_pct', 0)}%",
                "horizon": "7 days",
            }
            for kj in exec_kjs[:5]
        ]

    # Prediction markets
    kalshi = load_kalshi(wd)
    brief["prediction_markets"] = [
        {
            "ticker": m["ticker"],
            "yes_price_cents": round(m["yes_bid"] * 100),
            "mid_price_cents": round(m["mid_price"] * 100),
            "volume_dollars": m["volume"],
            "expiry": m["expiry"],
            "action": "BUY" if m["mid_price"] < 0.3 else "SELL" if m["mid_price"] > 0.7 else "HOLD",
            "implied_probability_pct": round(m["mid_price"] * 100),
        }
        for m in kalshi
    ]

    # Add Polymarket-style manual markets
    brief["prediction_markets"].extend([
        {"market": "WTI >$95 this week", "platform": "polymarket", "probability": 0.97, "volume": 357000, "expiry": "2026-05-16", "note": "Near certain — Iran deadline Thursday"},
        {"market": "WTI >$100 in May", "platform": "polymarket", "probability": 0.74, "volume": 12000000, "expiry": "2026-05-31", "note": "Iran escalation risk"},
        {"market": "US-Iran peace deal by Dec 31", "platform": "polymarket", "probability": 0.68, "volume": 102000000, "expiry": "2026-12-31", "note": "Broad market"},
        {"market": "Iran uranium handover by Dec 31", "platform": "polymarket", "probability": 0.45, "volume": 50000000, "expiry": "2026-12-31", "note": "Key condition"},
    ])

    # Watch items
    brief["watch_items"] = [
        {"id": "W-1", "item": "Trump-Xi summit outcomes (Wed-Fri)", "timeframe": "72h", "impact": "high"},
        {"id": "W-2", "item": "Iran ceasefire deadline — uranium handover refusal", "timeframe": "72h", "impact": "high"},
        {"id": "W-3", "item": "Oil price $120 breach — emerging market stress", "timeframe": "24-72h", "impact": "high"},
        {"id": "W-4", "item": "UK GDP data (Thursday)", "timeframe": "72h", "impact": "medium"},
        {"id": "W-5", "item": "US CPI data (Tuesday) — hot print risk", "timeframe": "24h", "impact": "medium"},
    ]

    # Indicator dashboard
    brief["indicators"] = {
        "hormuz_commercial_traffic": {"status": "near-zero", "trend": "stable", "threshold": ">50% of normal", "assessment": "high"},
        "brent_crude": {"status": f"$115-120", "trend": "rising", "threshold": "$120 breach", "assessment": "critical"},
        "us_europe_alliance_health": {"status": "eroding", "trend": "worsening", "assessment": "critical"},
        "israel_lebanon_ceasefire": {"status": "failing", "trend": "worsening", "assessment": "high"},
        "china_taiwan_tensions": {"status": "elevated", "trend": "stable", "assessment": "moderate"},
    }

    # Save
    EXPORTS.mkdir(parents=True, exist_ok=True)
    out_path = EXPORTS / f"agent-brief-{date_str}.json"
    out_path.write_text(json.dumps(brief, indent=2))
    log(f"Saved: {out_path} ({out_path.stat().st_size // 1024} KB)")

    # Also update latest.json (symlink or copy)
    latest_path = EXPORTS / "latest.json"
    latest_path.write_text(json.dumps(brief, indent=2))
    log(f"Updated: latest.json")

    return brief


def post_to_moltbook(brief, wd):
    """Post the brief to Moltbook as a structured thread."""
    api_key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not api_key:
        log("No MOLTBOOK_API_KEY — skipping Moltbook post")
        return

    date_str = dt.date.today().strftime("%Y-%m-%d")
    kj_count = len(brief.get("cross_cutting_analysis", {}).get("key_judgments", []))
    market_count = len(brief.get("prediction_markets", []))

    # Build the post content
    lines = [
        f"## GSIB Agent Brief — {date_str}",
        "",
        f"**Classification:** {brief['classification']}",
        f"**TTL:** {brief['ttl_hours']}h  |  **Theatres:** {brief['theatre_count']}  |  **Judgments:** {kj_count}  |  **Markets:** {market_count}",
        "",
        "---",
        "### Cross-Cutting Assessment",
        "",
        brief.get("cross_cutting_analysis", {}).get("bluf", ""),
        "",
        "### Key Judgments (7-Day Horizon)",
    ]

    for kj in brief.get("cross_cutting_analysis", {}).get("key_judgments", [])[:5]:
        lines.append(f"- **[{kj['region']}]** [{kj['band']}] {kj['probability']} — {kj['statement']}")

    lines += ["", "---", "### Prediction Markets"]

    for pm in brief.get("prediction_markets", [])[:6]:
        if "market" in pm:
            lines.append(f"- {pm['market']}: {pm['probability']*100:.0f}% ({pm.get('note', '')})")
        else:
            lines.append(f"- {pm['ticker']}: {pm['implied_probability_pct']}% YES @ ${pm['mid_price_cents']}¢ (vol: ${pm['volume_dollars']:,})")

    lines += ["", "---", "### Watch Items"]
    for wi in brief.get("watch_items", []):
        lines.append(f"- [{wi['timeframe']}] [{wi['impact']}] {wi['item']}")

    lines += ["", "---", f"*Full structured JSON: `{date_str}` | Schema: agent-brief/v1*"]

    content = "\n".join(lines)

    # Post to Moltbook
    payload = json.dumps({
        "title": f"GSIB Agent Brief — {date_str}",
        "content": content,
        "submolt": "agents",
    }).encode()

    req = urllib.request.Request(
        "https://www.moltbook.com/api/v1/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        post_url = f"https://www.moltbook.com/posts/{result['post']['id']}"
        log(f"Posted to Moltbook: {post_url}")
        brief["moltbook_url"] = post_url
        return post_url
    except urllib.error.HTTPError as e:
        log(f"Moltbook post failed: {e.code} — {e.read().decode(errors='replace')[:200]}")
        return None


def main():
    # Load .env for MOLTBOOK_API_KEY
    _env = REPO / ".env"
    if _env.exists():
        for _line in _env.read_text().splitlines():
            if _line.startswith("MOLTBOOK_API_KEY="):
                os.environ.setdefault("MOLTBOOK_API_KEY", _line.split("=", 1)[1].strip())
                break

    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--moltbook", action="store_true", help="Post to Moltbook")
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    brief = build(wd)

    if args.moltbook:
        post_to_moltbook(brief, wd)

    print(f"\n✅ Agent brief built: {len(brief['theatres'])} theatres, {len(brief['cross_cutting_analysis'].get('key_judgments', []))} judgments, {len(brief['prediction_markets'])} markets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
