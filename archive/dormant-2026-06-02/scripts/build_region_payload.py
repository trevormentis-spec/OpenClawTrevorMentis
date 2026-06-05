#!/usr/bin/env python3
"""Build region analysis payload and save to file."""
import sys, json, re
from pathlib import Path

region = sys.argv[1]
working_dir = Path(sys.argv[2])
out_path = Path(sys.argv[3])

# Load prompts
workspace = Path('/home/ubuntu/.openclaw/workspace')
md = (workspace / 'skills/daily-intel-brief/references/deepseek-prompts.md').read_text()
m = re.search(r'```\n(.*?)```', md, re.DOTALL)
system = m.group(1).strip() if m else ''

parts = md.split('## Regional Analyst Prompt')
rt = parts[1].split('```')[1].strip() if len(parts) > 1 and '```' in parts[1] else ''

# Load incidents
with open(working_dir / 'raw/incidents.json') as f:
    incidents = json.load(f).get('incidents', [])

LABELS = {
    'south_east_asia': 'South East Asia', 'oceania': 'Oceania',
    'east_asia': 'East Asia', 'south_asia': 'South Asia',
    'prediction_markets': 'Prediction Markets',
    'middle_east': 'Middle East', 'central_asia': 'Central Asia'
}
SHORTS = {
    'south_east_asia': 'SEA', 'oceania': 'OCE', 'east_asia': 'EAS',
    'south_asia': 'SAS', 'prediction_markets': 'PRD',
    'middle_east': 'ME', 'central_asia': 'CAS'
}

ri = [i for i in incidents if i.get('region') == region]
label = LABELS.get(region, region)
short = SHORTS.get(region, region[:3].upper())

user = rt.replace('{date_utc}', '2026-05-27')
user = user.replace('{region_label}', label)
user = user.replace('{region_snake}', region)
user = user.replace('{region_short}', short)
user = user.replace('{incidents_json_for_region}', json.dumps(ri, indent=2))
user = user.replace('{low_incident_warning}', '')
user = user.replace('{iw_board}', 'No standing I&W board.')

# Truncate to keep total under 19KB
MAX_TOTAL = 19000
for trunc_to in [15000, 12000, 10000, 8000, 6000, 4000]:
    u2 = user[:trunc_to] + '\n\n[DATA TRUNCATED]' if len(user) > trunc_to else user
    est = len(json.dumps({'model': 'x', 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': u2}]}).encode())
    if est <= MAX_TOTAL:
        user = u2
        break

# Add explicit JSON instruction
user += '\n\nIMPORTANT: Respond ONLY with a valid JSON object. No other text.'

payload = {
    'model': 'deepseek-v4-pro',
    'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
    'temperature': 0.3,
    'max_tokens': 16384,
}

print(f'[{region}] {len(ri)} incidents, user={len(user)} chars, total={len(json.dumps(payload).encode())} bytes')
out_path.write_text(json.dumps(payload))
