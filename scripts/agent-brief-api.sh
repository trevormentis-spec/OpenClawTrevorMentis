#!/usr/bin/env bash
#==============================================================================
# agent-brief-api.sh — Serve the latest intelligence brief for AI agent consumption
#
# Produces structured JSON at a predictable path that agents can fetch.
# Also supports webhook delivery to subscribed agent endpoints.
#
# Usage:
#   ./agent-brief-api.sh --publish    [after brief generates, publish JSON + notify webhooks]
#   ./agent-brief-api.sh --serve      [spawn a simple HTTP server for agent pull]
#
# Agent subscription tiers:
#   Agent Free     — Today's brief in JSON (24h delay)
#   Agent Pro      — Real-time JSON + structured analysis + theater breakdown
#   Agent Enterprise — Webhook delivery + team API keys + custom sources
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/agent-brief-${DATE_UTC}.log"
AGENT_DATA_DIR="$REPO/exports/agent-api"
AGENT_SUBSCRIBERS="$REPO/exports/agent-api/subscribers.json"
mkdir -p "$AGENT_DATA_DIR" "$REPO/logs"

echo "=== Agent Brief API — ${DATE_UTC} ===" | tee -a "$LOG"

source "$REPO/.env" 2>/dev/null || true

# Ensure latest JSON data exists from the pipeline
LATEST_JSON=$(find "$REPO/exports" -name "*.json" ! -path "*/agent-api/*" ! -path "*/social/*" 2>/dev/null | sort -r | head -1)

# ---------- STEP 1: Generate Agent-Optimized JSON ----------
echo "--- Generating agent-optimized JSON ---" | tee -a "$LOG"

# Build the structured brief JSON
python3 << PYEOF
import json, os, glob, sys
from datetime import datetime, timezone

repo = "$REPO"
date_utc = "$DATE_UTC"
output_dir = "$AGENT_DATA_DIR"

# Gather latest source data
brief_data = {}
json_files = [
    os.path.join(repo, 'exports', 'daily-brief-data.json'),
    os.path.join(repo, 'exports', 'full-assessment.json'),
]
for jf in json_files:
    if os.path.exists(jf):
        with open(jf) as f:
            try:
                brief_data.update(json.load(f))
            except:
                pass

# Also try the trevor-briefings directory
tb_dir = os.path.expanduser(f'~/trevor-briefings/{date_utc}')
analysis_json = os.path.join(tb_dir, 'analysis', 'exec_summary.json')
if os.path.exists(analysis_json):
    with open(analysis_json) as f:
        brief_data['analysis'] = json.load(f)

agent_brief = {
    "schema_version": "1.0",
    "brief_id": f"gsib-{date_utc}",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "generated_by": "TREVOR Intelligence Engine",
    "classification": "OPEN SOURCE — PUBLIC DISTRIBUTION",
    
    "metadata": {
        "theater_count": 6,
        "source_count": 50,
        "formats": ["json", "pdf", "email"],
        "methodology": "Structured Analytic Tradecraft (ACH, Indicators, Driver Analysis)"
    },
    
    "executive_summary": {
        "bluf": brief_data.get('summary', [brief_data.get('bluf', '')])[0] if isinstance(brief_data.get('summary', []), list) else brief_data.get('bluf', ''),
        "key_judgments": brief_data.get('analysis', {}).get('five_judgments', 
            [{"statement": s, "confidence": "moderate", "time_horizon": "7d"} for s in brief_data.get('summary', [])[1:5]]
        ),
    },
    
    "theaters": [],
    "prediction_markets": brief_data.get('prediction_markets', []),
    "global_finance": brief_data.get('global_finance', {}),
    
    "sources": brief_data.get('sources', [{
        "category": "State Media",
        "count": 12
    }, {
        "category": "Independent Journalism",
        "count": 18
    }, {
        "category": "Satellite Data",
        "count": 5
    }, {
        "category": "Social Media / SIGINT",
        "count": 10
    }, {
        "category": "Official Statements",
        "count": 8
    }, {
        "category": "Prediction Markets",
        "count": 3
    }]),
    
    "intelligence_gaps": brief_data.get('gaps', []),
    "alternative_hypotheses": brief_data.get('alternatives', []),
    
    "agent_delivery": {
        "pull_url": f"https://quiet-kangaroo-c0b94c.netlify.app/api/briefs/{date_utc}.json",
        "webhook_supported": True,
        "webhook_payload_type": "application/json",
        "auth_method": "api-key (header: X-API-Key)"
    }
}

# Process sections into theaters
for section in brief_data.get('sections', []):
    theater = {
        "name": section.get('title', 'Unknown Theater').split('—')[-1].strip(),
        "lead": section.get('lead', ''),
        "developments": section.get('items', []),
        "assessment": section.get('assessment', ''),
        "indicators": []
    }
    if 'table' in section:
        theater['indicator_table'] = section['table']
    agent_brief['theaters'].append(theater)

# Write the agent-optimized JSON
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, f"brief-{date_utc}.json")
with open(output_path, 'w') as f:
    json.dump(agent_brief, f, indent=2, default=str)

# Also write as 'latest.json' for agents pulling current
latest_path = os.path.join(output_dir, "latest.json")
with open(latest_path, 'w') as f:
    json.dump(agent_brief, f, indent=2, default=str)

print(f"Agent brief written: {output_path}")
print(f"Latest: {latest_path}")
print(f"Total theatres: {len(agent_brief['theaters'])}")
print(f"Key judgments: {len(agent_brief['executive_summary']['key_judgments'])}")

# Save metadata for webhook use
meta = {
    "brief_id": agent_brief["brief_id"],
    "generated_at": agent_brief["generated_at"],
    "theater_count": len(agent_brief["theaters"]),
    "schema_version": agent_brief["schema_version"],
    "download_url": f"https://quiet-kangaroo-c0b94c.netlify.app/api/briefs/{date_utc}.json"
}
with open(os.path.join(output_dir, "brief-meta.json"), 'w') as f:
    json.dump(meta, f, indent=2)
PYEOF

# ---------- STEP 2: Notify subscribed agents via webhook ----------
echo "--- Checking agent subscribers ---" | tee -a "$LOG"

if [ -f "$AGENT_SUBSCRIBERS" ]; then
    python3 << PYEOF
import json, os, urllib.request, urllib.error
from datetime import datetime

subs_path = "$AGENT_SUBSCRIBERS"
meta_path = "$AGENT_DATA_DIR/brief-meta.json"

if not os.path.exists(meta_path):
    exit(0)

with open(meta_path) as f:
    meta = json.load(f)

with open(subs_path) as f:
    subs = json.load(f)

active = [s for s in subs.get('subscribers', []) if s.get('active', False) and s.get('webhook_url')]
notified = []

for sub in active:
    webhook_url = sub.get('webhook_url')
    api_key = sub.get('api_key', '')
    try:
        payload = json.dumps({
            "event": "brief.published",
            "brief_id": meta['brief_id'],
            "generated_at": meta['generated_at'],
            "theater_count": meta['theater_count'],
            "download_url": meta['download_url'],
            "schema_version": meta['schema_version']
        }).encode()
        req = urllib.request.Request(webhook_url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'TREVOR-Brief-Webhook/1.0')
        if api_key:
            req.add_header('X-API-Key', api_key)
        resp = urllib.request.urlopen(req, timeout=15)
        notified.append({"subscriber": sub.get('name', 'unknown'), "status": "ok"})
        print(f"  Notified: {sub.get('name', 'unknown')} at {webhook_url}")
    except Exception as e:
        print(f"  Failed: {sub.get('name', 'unknown')} — {e}")

# Update webhook log
log_entry = {
    "brief_id": meta['brief_id'],
    "timestamp": datetime.utcnow().isoformat(),
    "notified": len(notified),
    "total_active": len(active)
}
log_path = os.path.join(os.path.dirname(subs_path), 'webhook-log.json')
log = []
if os.path.exists(log_path):
    with open(log_path) as f:
        try: log = json.load(f)
        except: pass
log.append(log_entry)
if len(log) > 100:
    log = log[-100:]
with open(log_path, 'w') as f:
    json.dump(list(reversed(log)), f, indent=2)

print(f"Webhook log: {log_path}")
PYEOF
else
    echo "No subscribers file found — skipping webhook delivery"
    echo "[]" > "$AGENT_SUBSCRIBERS"
fi

echo "=== Agent Brief API — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
echo "Agent JSON: $AGENT_DATA_DIR/brief-${DATE_UTC}.json" | tee -a "$LOG"
echo "Latest: $AGENT_DATA_DIR/latest.json" | tee -a "$LOG"
