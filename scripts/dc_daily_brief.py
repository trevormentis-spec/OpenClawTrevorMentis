#!/usr/bin/env python3
"""
Data Center Security Daily Brief — DeepSeek V4 Pro analysis, AgentMail delivery.

Reads the DC registry + external threat data, produces an analytical brief,
and delivers via AgentMail.

Usage:
    python3 scripts/dc_daily_brief.py                       # Full run + delivery
    python3 scripts/dc_daily_brief.py --dry-run              # No delivery
    python3 scripts/dc_daily_brief.py --preview              # Print to stdout only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "analyst" / "knowledge" / "data_centers"
FEEDS_DIR = DATA_DIR / "feeds"
REGISTRY_FILE = DATA_DIR / "registry.json"
COLLECTION_FILE = DATA_DIR / "analysis" / "collection.json"
EXPORTS_DIR = REPO / "exports"
AGENTMAIL_SENDER = "trevor_mentis@agentmail.to"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Pro
MAX_TOKENS = 8192


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[dc-brief {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_bytes())
    except Exception:
        return {}


def load_satellite_data() -> dict:
    """Load latest satellite imagery batch results."""
    imagery_dir = DATA_DIR / "imagery"
    if not imagery_dir.exists():
        return {"summary": "Satellite monitoring not initialized"}
    
    # Find the most recent batch
    batches = sorted(imagery_dir.glob("batch-*.json"), reverse=True)
    if not batches:
        return {"summary": "No satellite batches run yet"}
    
    latest = json.loads(batches[0].read_bytes())
    results = latest.get("results", [])
    with_data = sum(1 for r in results if r.get("has_imagery"))
    without_data = sum(1 for r in results if not r.get("has_imagery"))
    errors = [r for r in results if r.get("error")]
    
    # Load state for totals
    state_file = imagery_dir / "monitor_state.json"
    state = {}
    if state_file.exists():
        state = json.loads(state_file.read_bytes())
    
    return {
        "summary": (
            f"Latest batch: {len(results)} Tier 1 sites checked "
            f"({with_data} with imagery, {without_data} failed, {len(errors)} errors). "
            f"Total Tier 1 sites monitored: {state.get('total_checked', 0)} / 305 "
            f"({state.get('sites_with_imagery', 0)} with imagery)"
        ),
        "recent_sites": [
            {"name": r["site"]["name"], "has_imagery": r.get("has_imagery"), "data_size_bytes": r.get("data_size_bytes"), "operator": r["site"]["operator"]}
            for r in results if r.get("site")
        ],
        "state": state,
    }


def build_prompt(registry: dict) -> str:
    """Build the analytical prompt for DeepSeek V4 Pro."""
    geo = registry.get("geography", {})
    totals = registry.get("totals", {})
    top_ops = registry.get("top_operators", {})
    dc_by_country = geo.get("dc_by_country", {})
    power_by_country = geo.get("power_by_country", {})

    # Top DC clusters
    top_clusters = "\n".join(
        f"  {c}: {n} facilities" for c, n in list(dc_by_country.items())[:15]
    )
    top_power = "\n".join(
        f"  {c}: {n} MW" for c, n in list(power_by_country.items())[:10]
    )
    top_ops_str = "\n".join(
        f"  {k}: {v} facilities" for k, v in list(top_ops.items())[:8]
    )

    # Load satellite imagery findings
    sat_data = load_satellite_data()
    sat_summary = sat_data.get("summary", "No satellite imagery checked yet")
    sat_recent = ""
    if sat_data.get("recent_sites"):
        sat_recent = "\n".join(
            f"  {s['name'][:40]:40s} {'✅' if s.get('has_imagery') else '❌'} {s.get('data_size_bytes','?')}b"
            for s in sat_data["recent_sites"][:10]
        )
    sat_text = sat_summary + (f"\n\nRecent satellite checks:\n{sat_recent}" if sat_recent else "")

    # Load risk scores, supply chain, construction
    risk_data = load_json(DATA_DIR / "facility_risk.json")
    supply_data = load_json(DATA_DIR / "supply_chain.json")
    construct_data = load_json(DATA_DIR / "construction_tracker.json")

    # Format risk distribution
    risk_dist = risk_data.get("distribution", {})
    risk_summary = "\n".join(f"  {b}: {c} facilities" for b, c in sorted(risk_dist.items()))
    
    # Top moderate-risk facilities
    mod_facilities = risk_data.get("facilities", [])[:10] if risk_data.get("facilities") else []
    # Filter to highest scored
    sorted_facs = sorted(mod_facilities, key=lambda x: x.get("risk",{}).get("score",0), reverse=True)[:8]
    risk_examples = "\n".join(
        f"  {f['risk']['score']}/100 {f['name'][:35]:35s} {f['operator'][:12]:12s} driver={f['risk']['driver']}"
        for f in sorted_facs
    )

    # Supply chain
    sc = f"""
- Transformer lead time: {supply_data.get('transformer_lead_time_months','?')} months ({supply_data.get('transformer_lead_time_trend','stable')})
- Switchgear lead time: {supply_data.get('switchgear_lead_time_months','?')} months
- Generator lead time: {supply_data.get('generator_lead_time_months','?')} months"""
    sc_notes = "\n".join(f"  • {n}" for n in supply_data.get("key_notes", []))

    # Construction tracker
    recent_builds = construct_data.get("recent_announcements", [])
    build_lines = "\n".join(
        f"  {b['company']:15s} {b['project'][:20]:20s} {b['location'][:25]:25s} {b.get('capacity_mw',0)}MW {b.get('status','?')}"
        for b in recent_builds
    )
    total_pipeline = construct_data.get('total_mw_in_pipeline', 0)

    prompt = f"""You are a data center security analyst producing a daily intelligence brief. You write in analyst-to-analyst voice — direct, opinionated, signal-dense.

Today's date: {dt.date.today().isoformat()}

## DATA CENTER GLOBAL REGISTRY

### Inventory
- Hyperscale hubs: {totals.get('hyperscale_hubs', '?')}
- Colocation facilities: {totals.get('colocation_facilities', '?')}
- Total census facilities: {totals.get('global_census_total', '?')}
- Subsea cables: {totals.get('subsea_cables', '?')}
- Subsea landing stations: {totals.get('subsea_landing_stations', '?')}
- Terrestrial fiber routes: {totals.get('terrestrial_fiber_routes', '?')}
- Internet exchanges: {totals.get('internet_exchanges', '?')}

### Top DC Clusters by Country
{top_clusters}

### Power Capacity by Country (Hyperscale, MW)
{top_power}

### Top Operators
{top_ops_str}

## FACILITY RISK SCORES

Composite scoring (grid 30% + hazard 25% + connectivity 20% + geopolitical 15% + power exposure 10%):

### Distribution
{risk_summary}

### Highest-Risk Facilities
{risk_examples}

### Drivers
Risk is driven primarily by grid constraints in the US, geopolitics in Hong Kong/China, and connectivity limitations in island markets. The Northern Virginia cluster (world's largest) is rated MODERATE due to PJM grid strain.

## SATELLITE IMAGERY (Sentinel-2)
{sat_text}

## SUPPLY CHAIN TRACKER
{sc}

Key notes:
{sc_notes}

## CONSTRUCTION PIPELINE
{total_pipeline} MW in active pipeline:

{build_lines}

## SECURITY THREAT VECTORS

The brief must cover these threat vectors where data exists:

1. **SUbsea Cable Security** — Are there known cable outages, repairs, or new disruptions? What cables serve the largest DC clusters?
2. **Power Grid Strain** — Which DC-heavy grids face capacity constraints? Interconnection queue backlogs? Energy price spikes?
3. **Natural Hazard Risk** — Which major DC clusters face earthquake, hurricane, flood, or wildfire risk this season?
4. **Physical Security** — Protests, construction disruptions, access incidents near major DC corridors.
5. **Cloud/Network Downtime** — Major provider outages affecting DC operations.
6. **Geopolitical Risk** — Data sovereignty laws, export controls, sanctions affecting DC operations.
7. **Fiber Route Risk** — Construction, cuts, or congestion on backbone routes serving DC clusters.
8. **Satellite Imagery** — Sentinel-2 NDVI change detection at Tier 1 hyperscale hubs. New construction, ground disturbance, flooding, or activity anomalies.

## OUTPUT FORMAT

Produce a structured text brief with sections:

══════════════════════════════════════════════════════════
  DATA CENTER SECURITY DAILY — [date]
══════════════════════════════════════════════════════════

═══ BLUF ═══
<one paragraph. The single most important security development for data center operations today.>

═══ SUbSEA CABLE INTELLIGENCE ═══
<What's happening with subsea cables that serve major DC hubs. New cables, repairs, outages, congestion.>

═══ POWER & GRID ═══
<Which DC clusters face grid constraints. Interconnection queues. Energy price movements.>

═══ NATURAL HAZARD WATCH ═══
<Active natural hazard threats to major DC clusters.>

═══ PHYSICAL SECURITY ═══
<Physical security incidents near data centers.>

═══ CLOUD & NETWORK ═══
<Major cloud provider status, fiber route disruptions.>

═══ ASSET WATCH ═══
<New DC announcements, construction starts, operator changes. Risk rating changes.>

═══ MARKET SIGNALS ═══
<Colo pricing trends, capacity availability, supply chain signals.>

════════════════════════════════════════════════════════════
DATA SOURCES
════════════════════════════════════════════════════════════
  • Global Data Center Census (Tier 1-3): {totals.get('global_census_total', '?')} facilities
  • Submarine Cable Map: {totals.get('subsea_cables', '?')} cables
  • Internet Exchange Database: {totals.get('internet_exchanges', '?')} IXes
  • Analysis: DeepSeek V4 Pro

-- Trevor | Data Center Security Desk | {dt.date.today().isoformat()}
"""
    return prompt


def call_deepseek(prompt: str) -> str | None:
    """Call DeepSeek V4 Pro for analysis."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        log("No DEEPSEEK_API_KEY")
        return None

    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "You are a data center security analyst. Produce structured intelligence briefs. Use the exact format specified."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"].strip()
            log(f"Analysis generated: {len(content)} chars")
            return content
    except Exception as e:
        log(f"API call failed: {e}")
        return None


def send_agentmail(to: str, subject: str, body: str) -> bool:
    """Send via AgentMail SDK."""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key:
        log("No AGENTMAIL_API_KEY")
        return False

    try:
        sys.path.insert(0, str(REPO / "skills" / "agentmail" / "scripts"))
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        response = client.inboxes.messages.send(
            inbox_id=AGENTMAIL_SENDER,
            to=[to],
            subject=subject,
            text=body,
        )
        if hasattr(response, 'message_id'):
            msg_id = response.message_id
        elif isinstance(response, dict):
            msg_id = response.get("message_id", str(response))
        else:
            msg_id = str(response)
        log(f"Sent via AgentMail: {msg_id}")
        return True
    except Exception as e:
        log(f"AgentMail send failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Data Center Security Daily Brief")
    parser.add_argument("--dry-run", action="store_true", help="No delivery")
    parser.add_argument("--preview", action="store_true", help="Print to stdout only")
    args = parser.parse_args()

    log("Building data center security daily brief...")

    # Load registry
    registry = load_json(REGISTRY_FILE)
    if not registry:
        log("No registry found — run dc_collectors.py --registry first")
        return 1

    # Build prompt and call AI
    prompt = build_prompt(registry)
    log(f"Prompt built: {len(prompt)} chars")

    analysis = call_deepseek(prompt)
    if not analysis:
        log("Analysis generation failed")
        return 1

    # Save
    today = dt.date.today().isoformat()
    exports_path = EXPORTS_DIR / f"dc-daily-brief-{today}.txt"
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    exports_path.write_text(analysis)
    log(f"Saved: {exports_path} ({len(analysis)} chars)")

    if args.preview:
        print(analysis)
        return 0

    # Deliver
    if not args.dry_run:
        subject = f"Data Center Security Daily — {today}"
        delivered = send_agentmail("roderick.jones@gmail.com", subject, analysis)
        if delivered:
            log("Delivery successful ✅")
        else:
            log("Delivery failed ❌")
            return 1
    else:
        log("Dry run — no delivery")

    log("Data center security daily complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
